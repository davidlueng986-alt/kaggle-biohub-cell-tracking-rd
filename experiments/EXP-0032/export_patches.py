#!/usr/bin/env python3
"""EXP-0032: export cell-centered 3D patches + hard negatives for FUTURE GPU training.

Positives: one patch per GT node (all 6 subset samples, all GT frames, no striding).
Negatives (1:1 per frame, half/half):
  - bright-max: bright non-GT local maxima (cheap max-filter, NOT recomputed DoG)
  - random-bg: uniform random background locations
Output (gitignored): data/patches/<embryo>/patches.npy (uint16, (N,16,48,48),
  row-aligned with MANIFEST.csv) + data/patches/MANIFEST.csv
Splits are embryo-grouped (44b6 / 6bba) so future training can do PROTOCOL v1.1
embryo-grouped CV directly (never sample-wise splits).

Deterministic: sorted iteration everywhere, fixed seed (0).
CPU-only. No model training here.

Usage: python3 experiments/EXP-0032/export_patches.py [--out data/patches] [--seed 0]
"""
import argparse
import csv
import json
import sys
import time
import pathlib

import numpy as np
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Patch size (z,y,x): cells ~10um => ~6 z x ~25 y/x voxels at
# z=1.625 / y=x=0.40625 um/voxel. 16x48x48 ~= 2.6x cell diameter per axis:
# full cell + local context for a detector, while 1 patch = 36,864 vox = 72 KiB
# uint16 (6388 patches total ~= 470 MB, well under the 2 GB cap).
PZ, PY, PX = 16, 48, 48
SEED = 0
# Negative mining: cheap 3D max-filter footprint (~cell radius, odd sizes).
MAXF_SIZE = (3, 9, 9)
# Brightness floor for bright-max candidates: per-frame 98th percentile.
BRIGHT_PCTL = 98.0
# Exclusion box (Chebyshev half-widths, z/y/x) around GT centroids: negatives
# must stay clear of annotated cells. NOTE: GT is sparse/incomplete, so
# unannotated cells can still leak into negatives (documented caveat).
EXCL = (4, 12, 12)


def load_gt(path):
    d = json.loads(pathlib.Path(path).read_text())
    return d["nodes"]


def extract_patch(frame, z, y, x):
    """Fixed-size (PZ,PY,PX) patch centred at (z,y,x), zero-padded at borders."""
    Z, Y, X = frame.shape
    hz, hy, hx = PZ // 2, PY // 2, PX // 2
    z0, y0, x0 = z - hz, y - hy, x - hx
    patch = np.zeros((PZ, PY, PX), dtype=np.uint16)
    sz0, sy0, sx0 = max(0, z0), max(0, y0), max(0, x0)
    sz1, sy1, sx1 = min(Z, z0 + PZ), min(Y, y0 + PY), min(X, x0 + PX)
    dz0, dy0, dx0 = sz0 - z0, sy0 - y0, sx0 - x0
    patch[dz0:dz0 + (sz1 - sz0), dy0:dy0 + (sy1 - sy0),
          dx0:dx0 + (sx1 - sx0)] = frame[sz0:sz1, sy0:sy1, sx0:sx1]
    return patch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "patches"))
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    rng = np.random.default_rng(args.seed)
    t_start = time.time()

    import zarr
    subset = (ROOT / "data" / "SUBSET_IDS.txt").read_text().split()
    samples = sorted(subset)
    assert len(samples) == 6, f"expected 6 subset samples, got {samples}"

    # split -> {"patches": [...], "rows": [...]}
    acc = {}
    n_frames_read = 0
    for sid in samples:
        embryo = sid.split("_")[0]
        nodes = load_gt(ROOT / "experiments" / "EXP-0003" / "gt" / f"{sid}_gt.json")
        by_t = {}
        for n in nodes:
            by_t.setdefault(int(n["t"]), []).append(n)
        grp = zarr.open_group(str(ROOT / "data" / "train" / f"{sid}.zarr"), mode="r")["0"]
        T, Z, Y, X = grp.shape
        assert (Z, Y, X) == (64, 256, 256), grp.shape
        slot = acc.setdefault(embryo, {"patches": [], "rows": []})
        for t in sorted(by_t):
            frame = np.asarray(grp[int(t)])
            n_frames_read += 1
            gtn = sorted(by_t[t], key=lambda n: n["id"])
            # --- positives ---
            for n in gtn:
                slot["patches"].append(extract_patch(frame, n["z"], n["y"], n["x"]))
                slot["rows"].append({"label": 1, "embryo": embryo, "sample": sid,
                                     "t": t, "z": n["z"], "y": n["y"], "x": n["x"],
                                     "node_id": n["id"], "neg_type": ""})
            # --- negatives: 1:1 vs positives on this frame, half/half ---
            n_pos = len(gtn)
            n_bright = n_pos // 2
            n_rand = n_pos - n_bright
            # exclusion mask around GT centroids
            excl = np.zeros_like(frame, dtype=bool)
            for n in gtn:
                z0 = max(0, n["z"] - EXCL[0]); z1 = min(Z, n["z"] + EXCL[0] + 1)
                y0 = max(0, n["y"] - EXCL[1]); y1 = min(Y, n["y"] + EXCL[1] + 1)
                x0 = max(0, n["x"] - EXCL[2]); x1 = min(X, n["x"] + EXCL[2] + 1)
                excl[z0:z1, y0:y1, x0:x1] = True
            # bright non-GT local maxima
            mx = ndi.maximum_filter(frame, size=MAXF_SIZE)
            thr = float(np.percentile(frame, BRIGHT_PCTL))
            cand = np.argwhere((frame == mx) & (frame >= thr) & (~excl))
            cand = cand[np.lexsort((cand[:, 2], cand[:, 1], cand[:, 0]))]  # deterministic order
            take = []
            if len(cand) > 0 and n_bright > 0:
                k = min(n_bright, len(cand))
                take = [tuple(c) for c in cand[rng.choice(len(cand), size=k, replace=False)]]
            for (cz, cy, cx) in take:
                slot["patches"].append(extract_patch(frame, int(cz), int(cy), int(cx)))
                slot["rows"].append({"label": 0, "embryo": embryo, "sample": sid,
                                     "t": t, "z": int(cz), "y": int(cy), "x": int(cx),
                                     "node_id": -1, "neg_type": "bright_max"})
            # top-up shortfall + random-bg share with uniform random locations
            n_rand_total = n_rand + (n_bright - len(take))
            hz, hy, hx = PZ // 2, PY // 2, PX // 2
            for _ in range(n_rand_total):
                for _attempt in range(100):  # rejection-sample outside exclusion
                    cz = int(rng.integers(hz, Z - hz))
                    cy = int(rng.integers(hy, Y - hy))
                    cx = int(rng.integers(hx, X - hx))
                    if not excl[cz, cy, cx]:
                        break
                slot["patches"].append(extract_patch(frame, cz, cy, cx))
                slot["rows"].append({"label": 0, "embryo": embryo, "sample": sid,
                                     "t": t, "z": cz, "y": cy, "x": cx,
                                     "node_id": -1, "neg_type": "random_bg"})

    # --- write ---
    out.mkdir(parents=True, exist_ok=True)
    man_path = out / "MANIFEST.csv"
    total = 0
    with open(man_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["split", "idx_in_split", "label", "embryo", "sample",
                    "t", "z", "y", "x", "node_id", "neg_type"])
        for split in sorted(acc):
            arr = np.stack(acc[split]["patches"]).astype(np.uint16)
            sdir = out / split
            sdir.mkdir(parents=True, exist_ok=True)
            np.save(sdir / "patches.npy", arr)
            for i, r in enumerate(acc[split]["rows"]):
                w.writerow([split, i, r["label"], r["embryo"], r["sample"],
                            r["t"], r["z"], r["y"], r["x"], r["node_id"], r["neg_type"]])
            total += len(arr)
            print(f"split {split}: N={len(arr)} "
                  f"pos={sum(r['label'] == 1 for r in acc[split]['rows'])} "
                  f"neg={sum(r['label'] == 0 for r in acc[split]['rows'])} "
                  f"shape={arr.shape} bytes={arr.nbytes}")
    size_b = sum(p.stat().st_size for p in out.rglob("*.npy")) + man_path.stat().st_size
    dt = time.time() - t_start
    print(f"TOTAL patches={total} frames_read={n_frames_read} "
          f"disk={size_b / 1e6:.1f} MB elapsed={dt:.1f}s")
    print(f"wrote {man_path}")


if __name__ == "__main__":
    main()
