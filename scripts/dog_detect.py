#!/usr/bin/env python3
"""DoG detection probe (EXP-0007, CPU-only, deterministic).

Reads one zarr timepoint, applies Difference-of-Gaussians tuned to ~10um
cells (sigma_small=(1,3,3), sigma_large=(1.6,5,5) vox), thresholds the
response at a percentile, labels connected components, size-filters, and
emits integer voxel centroids.

Usage:
  python3 scripts/dog_detect.py data/train/SID.zarr --t 0 --out det.json
  python3 scripts/dog_detect.py data/train/SID.zarr --t 0 --pct 99.5 --min-size 50

Output: {"nodes":[{id,t,z,y,x}...], "params":{...}, "elapsed_s":...}
Honesty note: GT is SPARSE — unmatched detections are usually real cells,
not false positives. Recall vs GT is the meaningful number; "precision" is
reported as match-rate lower bound only.
"""
import json
import sys
import time

SIG_SMALL = (1.0, 3.0, 3.0)
SIG_LARGE = (1.6, 5.0, 5.0)


def detect(vol, pct=99.5, min_size=50, max_size=50000,
           sig_small=SIG_SMALL, sig_large=SIG_LARGE):
    import numpy as np
    from scipy.ndimage import gaussian_filter, label
    t0 = time.time()
    v = np.asarray(vol, dtype=np.float32)
    dog = gaussian_filter(v, sig_small) - gaussian_filter(v, sig_large)
    thr = float(np.percentile(dog, pct))
    bw = dog >= thr
    lab, n = label(bw)
    sizes = np.bincount(lab.ravel())
    nodes = []
    for i in range(1, n + 1):
        s = int(sizes[i])
        if not (min_size <= s <= max_size):
            continue
        z, y, x = np.argwhere(lab == i).mean(axis=0)
        nodes.append((int(round(z)), int(round(y)), int(round(x))))
    nodes.sort()
    return nodes, {"pct": pct, "min_size": min_size, "max_size": max_size,
                   "thr": thr, "n_components": int(n),
                   "elapsed_s": round(time.time() - t0, 2)}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("zarr")
    ap.add_argument("--t", type=int, default=0)
    ap.add_argument("--pct", type=float, default=99.5)
    ap.add_argument("--min-size", type=int, default=50)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import zarr
    vol = zarr.open_group(a.zarr, mode="r")["0"][a.t]
    nodes, params = detect(vol, pct=a.pct, min_size=a.min_size)
    out = {"nodes": [{"id": i + 1, "t": a.t, "z": z, "y": y, "x": x}
                     for i, (z, y, x) in enumerate(nodes)]}
    out["params"] = params
    json.dump(out, open(a.out, "w"))
    print(f"wrote {a.out}: {len(nodes)} detections "
          f"(thr={params['thr']:.1f}, {params['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
