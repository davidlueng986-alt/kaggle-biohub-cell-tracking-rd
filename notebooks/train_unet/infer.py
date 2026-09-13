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
  python3 infer.py --weights unet_best.pt --zarr data/train/6bba_05b6850b.zarr \\
      --t-start 20 --t-end 21 --out pred.json --thr 0.5 --top-k 150 \\
      --max-det-per-frame 300 --ceiling 500
  python3 infer.py --self-test        # synthetic unit tests (v11: 4 checks)
  python3 infer.py --help

v11 count discipline (EXP-0035: 26025 det/frame flood -> edge/adj 0.0):
  --thr / --top-k (per frame) / --top-k-volume / --max-det-per-frame
  (density-prior cap, soft) / --ceiling (hard flood guard, truncate + loud
  warning, never silently exceeded). det/frame mean/max/min reported per
  sample + stored in output meta.
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
# v11 count discipline (EXP-0035: 26025 det/frame flood -> edge/adj 0.0).
# Usable band 1-150 det/frame (GT 0.5-12.3/frame across subset 6; DoG
# operates ~44-57/frame dense). Density-prior cap 300 (soft, warn+truncate);
# hard flood ceiling 500/frame (loud WARNING + truncate, never exceeded).
DEFAULT_TOP_K = None          # per-frame top-K by score (None = unlimited)
DEFAULT_TOP_K_VOLUME = None   # volume-level top-K by score (None = unlimited)
DEFAULT_MAX_DET_PER_FRAME = 300
HARD_CEILING_PER_FRAME = 500
# Candidate pre-cap: bounds NMS O(n^2) runtime on flood inputs. Only engages
# above 50k raw candidates (normal inputs never reach it); deterministic
# (score desc, coords asc). Logged whenever it engages.
CANDIDATE_PRE_CAP = 50000
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


def _warn(msg):
    """Count-discipline warnings always go to stderr (never silent)."""
    print(f"WARNING [count-discipline] {msg}", file=sys.stderr, flush=True)


def extract_peaks(prob, thr=DEFAULT_PEAK_THR, footprint=PEAK_FOOTPRINT,
                  halves=NMS_HALVES, top_k=DEFAULT_TOP_K,
                  max_det=DEFAULT_MAX_DET_PER_FRAME,
                  ceiling=HARD_CEILING_PER_FRAME):
    """Peaks = local maxima >= thr, greedy NMS dedup (min peak separation).

    v11 count discipline: after NMS, truncate to the tightest of
    (top_k, max_det, ceiling) — all applied on the score-desc ordering, so
    truncation keeps the most confident peaks. `ceiling` is the hard flood
    guard (always enforced when >= 1); every truncation is reported in the
    returned info dict AND logged to stderr (never silent).

    Returns (peaks, info) where peaks = [(z, y, x, score)] sorted by score
    desc, coords asc (deterministic), and info = {n_candidates, n_peaks_raw,
    n_peaks, truncated, capped_by, pre_capped}.
    """
    prob = np.asarray(prob, dtype=np.float32)
    mx = ndi.maximum_filter(prob, size=footprint)
    cand = np.argwhere((prob == mx) & (prob >= thr))
    info = {"n_candidates": int(len(cand)), "n_peaks_raw": 0, "n_peaks": 0,
            "truncated": 0, "capped_by": None, "pre_capped": False}
    if len(cand) == 0:
        return [], info
    order = sorted(range(len(cand)),
                   key=lambda i: (-float(prob[tuple(cand[i])]),
                                  int(cand[i][0]), int(cand[i][1]), int(cand[i][2])))
    if len(order) > CANDIDATE_PRE_CAP:
        # Flood guard for NMS runtime: keep the most confident candidates.
        order = order[:CANDIDATE_PRE_CAP]
        info["pre_capped"] = True
        _warn(f"candidate pre-cap: {info['n_candidates']} raw candidates "
              f"> {CANDIDATE_PRE_CAP}; NMS runs on top-{CANDIDATE_PRE_CAP} "
              f"by score")
    kept = []
    hz, hy, hx = halves
    for i in order:
        z, y, x = (int(cand[i][0]), int(cand[i][1]), int(cand[i][2]))
        if all(abs(z - kz) > hz or abs(y - ky) > hy or abs(x - kx) > hx
               for kz, ky, kx, _ in kept):
            kept.append((z, y, x, float(prob[z, y, x])))
    info["n_peaks_raw"] = len(kept)
    # Tightest cap wins; ceiling is the hard backstop (always applied).
    caps = []
    if top_k is not None and top_k >= 1:
        caps.append(("top_k", int(top_k)))
    if max_det is not None and max_det >= 1:
        caps.append(("max_det_per_frame", int(max_det)))
    if ceiling is not None and ceiling >= 1:
        caps.append(("ceiling", int(ceiling)))
    if caps:
        name, lim = min(caps, key=lambda c: c[1])
        if len(kept) > lim:
            info["truncated"] = len(kept) - lim
            info["capped_by"] = name
            kept = kept[:lim]
            _warn(f"frame truncated: {info['n_peaks_raw']} peaks -> {lim} "
                  f"(capped_by={name}, thr={thr})")
            if name == "ceiling":
                _warn(f"FLOOD-GUARD ENGAGED: raw peaks {info['n_peaks_raw']} "
                      f"exceeded hard ceiling {lim}; output truncated, "
                      f"do NOT trust this frame's recall")
    info["n_peaks"] = len(kept)
    return kept, info


def _synth_heatmap(seed=0):
    """Shared synthetic heatmap: 5 strong peaks + 2 weak decoys + noise."""
    set_seed(seed)
    Z, Y, X = DEFAULT_PATCH_SHAPE
    rng = np.random.default_rng(seed)
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
    return prob, true


def run_self_test():
    """Unit tests (v11 = original recovery + flood-cap + thr monotonicity)."""
    # (0) Original EXP-0035 gate: 5 Gaussian peaks + 2 weak decoys.
    prob, true = _synth_heatmap(seed=0)
    got, info = extract_peaks(prob, thr=DEFAULT_PEAK_THR)
    assert len(got) == 5, f"expected 5 peaks, got {len(got)}: {got}"
    unmatched = list(true)
    for z, y, x, s in got:
        assert s >= DEFAULT_PEAK_THR, f"peak below thr: {(z, y, x, s)}"
        hit = [c for c in unmatched
               if abs(z - c[0]) <= 1 and abs(y - c[1]) <= 1 and abs(x - c[2]) <= 1]
        assert hit, f"peak {(z, y, x)} matches no true peak"
        unmatched.remove(hit[0])
    assert not unmatched, f"missed true peaks: {unmatched}"
    assert info["truncated"] == 0 and info["capped_by"] is None
    print(f"SELF-TEST PASS [recovery]: exactly 5/5 peaks "
          f"(+2 sub-threshold decoys correctly ignored)")

    # (a) v11 flood-cap: uniform-high noise heatmap must hit the ceiling,
    # get truncated, and say so (warning + info flags, never silent).
    rng = np.random.default_rng(1)
    flood = (0.80 + 0.19 * rng.random(DEFAULT_PATCH_SHAPE)).astype(np.float32)
    fgot, finfo = extract_peaks(flood, thr=0.3, top_k=None,
                                max_det=10**9, ceiling=50)
    assert finfo["n_peaks_raw"] > 50, \
        f"flood fixture too tame: raw={finfo['n_peaks_raw']}"
    assert len(fgot) == 50, f"ceiling not enforced: got {len(fgot)}"
    assert finfo["capped_by"] == "ceiling" and finfo["truncated"] > 0, finfo
    print(f"SELF-TEST PASS [flood-cap]: raw={finfo['n_peaks_raw']} capped "
          f"to 50 by ceiling (truncated={finfo['truncated']})")

    # (b) v11 threshold monotonicity: raising thr never adds detections.
    thrs = [0.1, 0.3, 0.5, 0.7, 0.9]
    counts = [len(extract_peaks(prob, thr=t,
                                max_det=None, ceiling=None)[0]) for t in thrs]
    assert all(b <= a for a, b in zip(counts, counts[1:])), \
        f"thr not monotone: {list(zip(thrs, counts))}"
    assert counts[0] >= counts[-1] and counts[0] >= 5 and counts[-1] <= 5, \
        f"unexpected sweep: {list(zip(thrs, counts))}"
    print(f"SELF-TEST PASS [thr-monotone]: "
          + ", ".join(f"thr={t}:{n}" for t, n in zip(thrs, counts)))

    # (c) v11 top-K: keeps the most confident peaks, deterministic order.
    kgot, kinfo = extract_peaks(prob, thr=DEFAULT_PEAK_THR, top_k=3,
                                max_det=None, ceiling=None)
    assert len(kgot) == 3 and kinfo["capped_by"] == "top_k", kinfo
    scores = [s for _, _, _, s in kgot]
    assert all(b <= a for a, b in zip(scores, scores[1:])), scores
    print(f"SELF-TEST PASS [top-k]: 5 peaks -> top-3 by score, "
          f"order desc { [round(s, 3) for s in scores] }")
    print("SELF-TEST PASS: 4/4 checks (recovery, flood-cap, "
          "thr-monotone, top-k)")
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
    ap.add_argument("--top-k", type=int, default=None,
                    help="per-frame top-K by score (def: no per-frame top-K)")
    ap.add_argument("--top-k-volume", type=int, default=None,
                    help="volume-level top-K by score over emitted frames")
    ap.add_argument("--max-det-per-frame", type=int, default=DEFAULT_MAX_DET_PER_FRAME,
                    help="density-prior cap per frame (0/neg = disable; "
                         "ceiling still guards)")
    ap.add_argument("--ceiling", type=int, default=HARD_CEILING_PER_FRAME,
                    help="HARD flood ceiling per frame (truncate + loud "
                         "warning; never silently exceeded)")
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
    top_k = a.top_k if a.top_k is not None else DEFAULT_TOP_K
    top_k_vol = a.top_k_volume if a.top_k_volume is not None \
        else DEFAULT_TOP_K_VOLUME
    max_det = a.max_det_per_frame
    if max_det is not None and max_det <= 0:
        max_det = None  # explicitly disabled; ceiling still guards
    ceiling = a.ceiling
    assert ceiling is not None and ceiling >= 1, \
        f"--ceiling must be >= 1 (got {a.ceiling})"
    stride = tuple(p // 2 for p in patch_shape)

    if a.mean is not None and a.std is not None:
        gmean, gstd = float(a.mean), float(a.std)
        norm_src = "cli"
    else:
        gmean, gstd = train_stats(find_patches_dir(), DEFAULT_TRAIN_SPLIT)
        norm_src = f"train-split-{DEFAULT_TRAIN_SPLIT}"
    print(f"norm: mean={gmean:.2f} std={gstd:.2f} ({norm_src}) "
          f"patch={patch_shape} stride={stride} thr={thr} "
          f"top_k={top_k} top_k_volume={top_k_vol} "
          f"max_det_per_frame={max_det} ceiling={ceiling}", flush=True)

    nodes = []
    per_frame = []
    n_trunc_frames = 0
    n_ceiling_hits = 0
    import time
    t_start = time.time()
    for t in range(t0, t1 + 1):
        frame = np.asarray(grp[t]).astype(np.float32)
        heat = infer_heatmap(model, (frame - gmean) / gstd,
                             patch_shape, stride, a.batch, device)
        peaks, pinfo = extract_peaks(heat, thr=thr, top_k=top_k,
                                     max_det=max_det, ceiling=ceiling)
        for k, (z, y, x, s) in enumerate(peaks):
            nodes.append({"id": t * 1000000 + (k + 1), "t": t,
                          "z": z, "y": y, "x": x, "score": round(s, 4)})
        per_frame.append(len(peaks))
        if pinfo["truncated"]:
            n_trunc_frames += 1
        if pinfo["capped_by"] == "ceiling":
            n_ceiling_hits += 1
        print(f"t={t}: heat_max={heat.max():.3f} n_det={len(peaks)} "
              f"(raw={pinfo['n_peaks_raw']} capped_by={pinfo['capped_by']})",
              flush=True)
    if top_k_vol is not None and top_k_vol >= 1 and len(nodes) > top_k_vol:
        nodes.sort(key=lambda n: (-n["score"], n["t"], n["z"], n["y"], n["x"]))
        dropped = len(nodes) - top_k_vol
        nodes = nodes[:top_k_vol]
        _warn(f"volume top-K: dropped {dropped} lowest-score detections "
              f"(kept {top_k_vol})")
    dt = time.time() - t_start
    nodes.sort(key=lambda n: n["id"])
    n_frames = t1 - t0 + 1
    import statistics as _stats
    dpf_mean = sum(per_frame) / max(n_frames, 1)
    dpf_max = max(per_frame) if per_frame else 0
    dpf_min = min(per_frame) if per_frame else 0
    band, band_note = "USABLE", "within 1-150 det/frame band"
    if dpf_mean > HARD_CEILING_PER_FRAME:
        band, band_note = "FLOOD", "mean exceeds hard ceiling (should be impossible)"
    elif dpf_max > ceiling:
        band, band_note = "FLOOD", "a frame exceeded the ceiling (should be impossible)"
    elif dpf_mean > 150 or dpf_max > 300:
        band, band_note = "ABOVE-BAND", "above usable 1-150 band: count discipline suspect"
    print(f"det/frame: mean={dpf_mean:.1f} max={dpf_max} min={dpf_min} "
          f"over {n_frames} frames [{band}: {band_note}] "
          f"(truncated_frames={n_trunc_frames} ceiling_hits={n_ceiling_hits})",
          flush=True)
    out = {"nodes": nodes, "edges": [],
            "meta": {"weights": a.weights, "zarr": a.zarr,
                     "t_range": [t0, t1], "thr": thr,
                     "top_k": top_k, "top_k_volume": top_k_vol,
                     "max_det_per_frame": max_det, "ceiling": ceiling,
                     "patch_shape": list(patch_shape),
                     "stride": list(stride), "mean": gmean, "std": gstd,
                     "voxel_size_um": list(cfg.get("voxel_um", DEFAULT_VOXEL_UM)),
                     "det_per_frame": {"mean": round(dpf_mean, 2),
                                       "max": dpf_max, "min": dpf_min},
                     "truncated_frames": n_trunc_frames,
                     "ceiling_hits": n_ceiling_hits,
                     "band": band,
                     "seconds": round(dt, 1)}}
    with open(a.out, "w") as f:
        json.dump(out, f)
    print(f"wrote {a.out}: {len(nodes)} detections over {t1 - t0 + 1} frames "
          f"in {dt:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
