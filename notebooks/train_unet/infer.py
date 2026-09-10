#!/usr/bin/env python3
"""Learned 3D-UNet heatmap inference over full zarr frames (EXP-0035 eval).

Loads a train.py checkpoint (state_dict + cfg, map_location cpu), runs
sliding-window heatmap inference over FULL zarr frames, extracts peaks, and
writes a graph JSON {nodes:[{id,t,z,y,x}], edges:[]} — linking is done
downstream (run.sh imports baseline_link itself).

Conventions match notebooks/train_unet/train.py EXACTLY:
  - UNet/DC architecture verbatim (3-level, base 32 ch).
  - Normalisation uses TRAIN-embryo (6bba) global mean/std from data/patches
    (same streaming computation as PatchDataset; --mean/--std override).
  - patch_shape / patch_center / peak_thr / voxel_um taken from ckpt cfg
    (fall back to train.py CONFIG defaults for random-weight dry runs).
  - Sliding window: stride = half patch, deterministic tiling; overlapping
    heatmaps averaged; zero padding never needed (P <= frame dims, last
    window anchored at D-P).
  - Peaks: sigmoid >= thr + local maximum via maximum_filter footprint
    (3,9,9) + greedy NMS-ish dedup with min separation halves (1,4,4).

Imports: torch, numpy, scipy, zarr, stdlib ONLY (kernel-safe, offline).
Deterministic, CPU-only.

Usage:
  python3 infer.py --weights unet_best.pt --zarr data/train/6bba_05b6850b.zarr \\
      --t-start 20 --t-end 21 --out pred.json
  python3 infer.py --self-test        # synthetic peak-extraction unit test
  python3 infer.py --help
"""
import argparse
import json
import pathlib
import random
import sys

import numpy as np
import torch
import torch.nn as nn
from scipy import ndimage as ndi

DEFAULT_PATCH_SHAPE = (16, 48, 48)
DEFAULT_PATCH_CENTER = (8, 24, 24)
DEFAULT_PEAK_THR = 0.3
DEFAULT_VOXEL_UM = (1.625, 0.40625, 0.40625)
DEFAULT_TRAIN_SPLIT = "6bba"
PEAK_FOOTPRINT = (3, 9, 9)
# NMS min separation = footprint halves (Chebyshev, inclusive).
NMS_HALVES = tuple(s // 2 for s in PEAK_FOOTPRINT)  # (1, 4, 4)
BASE_CH = 32


def set_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass


class DC(nn.Module):
    def __init__(self, ci, co):
        super().__init__()
        self.n = nn.Sequential(nn.Conv3d(ci, co, 3, padding=1), nn.ReLU(inplace=True),
                               nn.Conv3d(co, co, 3, padding=1), nn.ReLU(inplace=True))

    def forward(self, x):
        return self.n(x)


class UNet(nn.Module):
    """3-level 3D UNet, base 32 ch. Verbatim copy of train.py (EXP-0035)."""

    def __init__(self, base=32):
        super().__init__()
        self.e0 = DC(1, base)
        self.d0 = nn.MaxPool3d(2)
        self.e1 = DC(base, base * 2)
        self.d1 = nn.MaxPool3d(2)
        self.e2 = DC(base * 2, base * 4)
        self.u1 = nn.ConvTranspose3d(base * 4, base * 2, 2, 2)
        self.c1 = DC(base * 4, base * 2)
        self.u0 = nn.ConvTranspose3d(base * 2, base, 2, 2)
        self.c0 = DC(base * 2, base)
        self.out = nn.Conv3d(base, 1, 1)

    def forward(self, x):
        a0 = self.e0(x)
        a1 = self.e1(self.d0(a0))
        m = self.e2(self.d1(a1))
        u = self.c1(torch.cat([self.u1(m), a1], 1))
        v = self.c0(torch.cat([self.u0(u), a0], 1))
        return self.out(v)


def load_model(weights_path, device):
    """Load ckpt {model, cfg, ep}; return (model, cfg_dict)."""
    ckpt = torch.load(str(weights_path), map_location=device, weights_only=False)
    cfg = dict(ckpt.get("cfg", {}))
    cfg.setdefault("patch_shape", DEFAULT_PATCH_SHAPE)
    cfg.setdefault("patch_center", DEFAULT_PATCH_CENTER)
    cfg.setdefault("peak_thr", DEFAULT_PEAK_THR)
    cfg.setdefault("voxel_um", DEFAULT_VOXEL_UM)
    cfg.setdefault("base_ch", BASE_CH)
    model = UNet(cfg["base_ch"])
    model.load_state_dict(ckpt["model"])
    model.to(device).eval()
    return model, cfg


def find_patches_dir():
    here = pathlib.Path(__file__).resolve().parents[2]
    for c in [here / "data" / "patches"]:
        if (c / "MANIFEST.csv").is_file():
            return str(c)
    raise FileNotFoundError("data/patches/MANIFEST.csv not found")


def train_stats(patches_dir, split=DEFAULT_TRAIN_SPLIT):
    """TRAIN-embryo global mean/std, streaming from memmap (== PatchDataset)."""
    import csv
    rows = [r for r in csv.DictReader(open(f"{patches_dir}/MANIFEST.csv"))
            if r["split"] == split]
    arr = np.load(f"{patches_dir}/{split}/patches.npy", mmap_mode="r")
    s = np.float64(0)
    s2 = np.float64(0)
    n = np.int64(0)
    for i in range(0, len(rows), 512):
        b = arr[i:i + 512].astype(np.float64)
        s += b.sum()
        s2 += (b ** 2).sum()
        n += b.size
    mean = float(s / n)
    std = float(np.sqrt(max(s2 / n - (s / n) ** 2, 1e-12)))
    return mean, std


def window_starts(D, P, S):
    """Deterministic tile starts covering [0, D) with windows of size P."""
    if P >= D:
        return [0]
    starts = list(range(0, D - P + 1, S))
    if starts[-1] != D - P:
        starts.append(D - P)
    return starts


@torch.no_grad()
def infer_heatmap(model, frame_norm, patch_shape, stride, batch, device):
    """Sliding-window heatmap over one (Z,Y,X) frame; overlaps averaged."""
    Z, Y, X = frame_norm.shape
    PZ, PY, PX = patch_shape
    SZ, SY, SX = stride
    zs, ys, xs = (window_starts(Z, PZ, SZ), window_starts(Y, PY, SY),
                  window_starts(X, PX, SX))
    heat = np.zeros((Z, Y, X), dtype=np.float32)
    count = np.zeros((Z, Y, X), dtype=np.float32)
    coords = [(z, y, x) for z in zs for y in ys for x in xs]
    for i in range(0, len(coords), batch):
        grp = coords[i:i + batch]
        inp = np.stack([frame_norm[z:z + PZ, y:y + PY, x:x + PX]
                        for z, y, x in grp]).astype(np.float32)
        out = torch.sigmoid(
            model(torch.from_numpy(inp).unsqueeze(1).to(device))).cpu().numpy()
        for (z, y, x), h in zip(grp, out):
            heat[z:z + PZ, y:y + PY, x:x + PX] += h[0]
            count[z:z + PZ, y:y + PY, x:x + PX] += 1.0
    return heat / np.maximum(count, 1e-6)


def extract_peaks(prob, thr=DEFAULT_PEAK_THR, footprint=PEAK_FOOTPRINT,
                  halves=NMS_HALVES):
    """Peaks = local maxima >= thr, greedy NMS dedup (min peak separation).

    Returns [(z, y, x, score)] sorted by score desc, coords asc (deterministic).
    """
    prob = np.asarray(prob, dtype=np.float32)
    mx = ndi.maximum_filter(prob, size=footprint)
    cand = np.argwhere((prob == mx) & (prob >= thr))
    if len(cand) == 0:
        return []
    order = sorted(range(len(cand)),
                   key=lambda i: (-float(prob[tuple(cand[i])]),
                                  int(cand[i][0]), int(cand[i][1]), int(cand[i][2])))
    kept = []
    hz, hy, hx = halves
    for i in order:
        z, y, x = (int(cand[i][0]), int(cand[i][1]), int(cand[i][2]))
        if all(abs(z - kz) > hz or abs(y - ky) > hy or abs(x - kx) > hx
               for kz, ky, kx, _ in kept):
            kept.append((z, y, x, float(prob[z, y, x])))
    return kept


def run_self_test():
    """Unit test: 5 Gaussian peaks + 2 weak decoys -> recover exactly the 5."""
    set_seed(0)
    Z, Y, X = DEFAULT_PATCH_SHAPE
    rng = np.random.default_rng(0)
    true = [(3, 10, 10), (5, 30, 35), (10, 12, 30), (12, 36, 12), (8, 24, 24)]
    decoy = [(4, 40, 8), (13, 8, 40)]
    zz, yy, xx = np.mgrid[0:Z, 0:Y, 0:X]
    prob = np.zeros((Z, Y, X), dtype=np.float32)
    sg = (1.5, 4.0, 4.0)
    for (cz, cy, cx) in true:
        g = (((zz - cz) / sg[0]) ** 2 + ((yy - cy) / sg[1]) ** 2
             + ((xx - cx) / sg[2]) ** 2)
        prob = np.maximum(prob, (0.9 * np.exp(-0.5 * g)).astype(np.float32))
    for (cz, cy, cx) in decoy:
        g = (((zz - cz) / sg[0]) ** 2 + ((yy - cy) / sg[1]) ** 2
             + ((xx - cx) / sg[2]) ** 2)
        prob = np.maximum(prob, (0.2 * np.exp(-0.5 * g)).astype(np.float32))
    prob += (0.01 * rng.standard_normal(prob.shape)).astype(np.float32)
    got = extract_peaks(prob, thr=DEFAULT_PEAK_THR)
    assert len(got) == 5, f"expected 5 peaks, got {len(got)}: {got}"
    unmatched = list(true)
    for z, y, x, s in got:
        assert s >= DEFAULT_PEAK_THR, f"peak below thr: {(z, y, x, s)}"
        hit = [c for c in unmatched
               if abs(z - c[0]) <= 1 and abs(y - c[1]) <= 1 and abs(x - c[2]) <= 1]
        assert hit, f"peak {(z, y, x)} matches no true peak"
        unmatched.remove(hit[0])
    assert not unmatched, f"missed true peaks: {unmatched}"
    print(f"SELF-TEST PASS: recovered exactly 5/5 peaks "
          f"(+2 sub-threshold decoys correctly ignored)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="UNet heatmap inference (EXP-0035)")
    ap.add_argument("--weights", default=None, help="ckpt .pt (state_dict+cfg)")
    ap.add_argument("--random-weights", action="store_true",
                    help="skip ckpt; use seeded random UNet (dry-run only)")
    ap.add_argument("--zarr", default=None, help="path to <sid>.zarr")
    ap.add_argument("--t-start", type=int, default=0)
    ap.add_argument("--t-end", type=int, default=None, help="inclusive")
    ap.add_argument("--out", default=None, help="output graph JSON")
    ap.add_argument("--mean", type=float, default=None)
    ap.add_argument("--std", type=float, default=None)
    ap.add_argument("--thr", type=float, default=None, help="peak thr (def: ckpt cfg)")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return run_self_test()

    if a.zarr is None or a.out is None:
        ap.error("--zarr and --out required (or use --self-test)")
    if a.weights is None and not a.random_weights:
        ap.error("provide --weights (or --random-weights for dry-run)")

    set_seed(a.seed)
    device = torch.device("cpu")
    import zarr
    grp = zarr.open_group(a.zarr, mode="r")["0"]
    T, Z, Y, X = grp.shape
    t0, t1 = a.t_start, a.t_end if a.t_end is not None else T - 1
    assert 0 <= t0 <= t1 < T, f"t range [{t0},{t1}] vs T={T}"

    if a.weights is not None:
        model, cfg = load_model(a.weights, device)
    else:
        cfg = {"patch_shape": DEFAULT_PATCH_SHAPE,
               "patch_center": DEFAULT_PATCH_CENTER,
               "peak_thr": DEFAULT_PEAK_THR, "voxel_um": DEFAULT_VOXEL_UM,
               "base_ch": BASE_CH}
        model = UNet(cfg["base_ch"]).to(device).eval()
    patch_shape = tuple(cfg["patch_shape"])
    thr = a.thr if a.thr is not None else float(cfg["peak_thr"])
    stride = tuple(p // 2 for p in patch_shape)

    if a.mean is not None and a.std is not None:
        gmean, gstd = float(a.mean), float(a.std)
        norm_src = "cli"
    else:
        gmean, gstd = train_stats(find_patches_dir(), DEFAULT_TRAIN_SPLIT)
        norm_src = f"train-split-{DEFAULT_TRAIN_SPLIT}"
    print(f"norm: mean={gmean:.2f} std={gstd:.2f} ({norm_src}) "
          f"patch={patch_shape} stride={stride} thr={thr}", flush=True)

    nodes = []
    import time
    t_start = time.time()
    for t in range(t0, t1 + 1):
        frame = np.asarray(grp[t]).astype(np.float32)
        heat = infer_heatmap(model, (frame - gmean) / gstd,
                             patch_shape, stride, a.batch, device)
        peaks = extract_peaks(heat, thr=thr)
        for k, (z, y, x, s) in enumerate(peaks):
            nodes.append({"id": t * 1000000 + (k + 1), "t": t,
                          "z": z, "y": y, "x": x, "score": round(s, 4)})
        print(f"t={t}: heat_max={heat.max():.3f} n_det={len(peaks)}", flush=True)
    dt = time.time() - t_start
    nodes.sort(key=lambda n: n["id"])
    out = {"nodes": nodes, "edges": [],
           "meta": {"weights": a.weights, "zarr": a.zarr,
                    "t_range": [t0, t1], "thr": thr, "patch_shape": list(patch_shape),
                    "stride": list(stride), "mean": gmean, "std": gstd,
                    "voxel_size_um": list(cfg.get("voxel_um", DEFAULT_VOXEL_UM)),
                    "seconds": round(dt, 1)}}
    with open(a.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {a.out}: {len(nodes)} detections over {t1 - t0 + 1} frames "
          f"in {dt:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
