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


def _split_component(idx, dog, min_size, peak_footprint, prominence=0.0):
    """Peak-split one oversize component. Returns list of voxel arrays, or
    None to keep the component whole. prominence: secondary peaks must reach
    >= prominence * primary peak value (EXP-0013; 0.0 = off, all separated
    peaks split). Small parts merge into the nearest big part (no loss)."""
    import numpy as np
    from scipy.ndimage import maximum_filter
    from scipy.spatial import cKDTree
    lo = idx.min(axis=0)
    sl = tuple(slice(int(a), int(b)) for a, b in zip(lo, idx.max(axis=0) + 1))
    crop = dog[sl]
    mask = np.zeros_like(crop, dtype=bool)
    mask[tuple((idx - lo).T)] = True
    mx = (maximum_filter(crop, size=peak_footprint) == crop) & mask
    cand = [tuple(p + lo) for p in np.argwhere(mx)]
    cand.sort(key=lambda p: -dog[p])
    fp = (np.array(peak_footprint, dtype=float) / 2.0) ** 2
    peaks = []
    for p in cand:
        pa = np.array(p, dtype=float)
        if all(float(sum(((pa - np.array(q)) ** 2) / fp)) >= 1.0 for q in peaks):
            peaks.append(p)
    if prominence > 0.0 and peaks:
        cut = float(dog[peaks[0]]) * prominence
        peaks = [p for p in peaks if float(dog[p]) >= cut]
    if len(peaks) < 2:
        return None
    tree = cKDTree(np.array(peaks, dtype=float))
    _, a = tree.query(idx.astype(float), k=1)
    big, small = [], []
    for k in range(len(peaks)):
        (big if len(idx[a == k]) >= min_size else small).append(k)
    if not big:
        return None
    out = [idx[a == k] for k in big]
    if small:
        rest = np.concatenate([idx[a == k] for k in small])
        btree = cKDTree(np.array([g.mean(axis=0) for g in out]))
        _, bi = btree.query(rest.astype(float), k=1)
        out = [np.concatenate([g, rest[bi == j]]) if np.any(bi == j) else g
               for j, g in enumerate(out)]
    return out


def detect(vol, pct=99.5, min_size=50, max_size=50000,
           sig_small=SIG_SMALL, sig_large=SIG_LARGE,
           split_size=None, peak_footprint=(5, 15, 15), prominence=0.0,
           thr_mode="percentile", k=12.0, downsample=1):
    """thr_mode: 'percentile' (thr = pct-th percentile of DoG, per-frame) or
    'mad' (thr = median + k*MAD — adapts to background spread, not tail mass;
    EXP-0022: heavy bright tails push percentiles up and delete dim cells).
    downsample: 2 = detect on 2x-downsampled y/x, map centroids back x2
    (H-005 timing path; min_size scaled by area; EXP-0022 measures recall
    parity + speedup)."""
    """split_size: components larger than this are peak-split (None=off).
    Peak-split: DoG local maxima (maximum_filter footprint) inside the
    component become seeds; voxels go to the nearest seed (cKDTree);
    parts < min_size merge into the nearest kept part (no voxel loss)."""
    import numpy as np
    from scipy.ndimage import gaussian_filter, label, maximum_filter
    t0 = time.time()
    v = np.asarray(vol, dtype=np.float32)
    ds_note = None
    if downsample == 2:
        from scipy.ndimage import zoom
        v = zoom(v, (1.0, 0.5, 0.5), order=1)
        min_size = max(8, min_size // 4)
        max_size = max_size // 4
        ds_note = "y/x half-res, sizes /4"
    dog = gaussian_filter(v, sig_small) - gaussian_filter(v, sig_large)
    if thr_mode == "mad":
        med = float(np.median(dog))
        mad = float(np.median(np.abs(dog - med))) + 1e-9
        thr = med + k * mad
    else:
        thr = float(np.percentile(dog, pct))
    bw = dog >= thr
    lab, n = label(bw)
    sizes = np.bincount(lab.ravel())
    parts = []  # list of (voxel-index array, split_flag, parent_comp)
    n_split = 0
    for i in range(1, n + 1):
        s = int(sizes[i])
        if not (min_size <= s <= max_size):
            continue  # too small: noise; too big w/o split: dropped as before
        idx = np.argwhere(lab == i)
        done = False
        if split_size is not None and s > split_size:
            got = _split_component(idx, dog, min_size, peak_footprint,
                                   prominence)
            if got is not None:
                parts.extend([(g, True, i) for g in got])
                n_split += 1
                done = True
        if not done:
            parts.append((idx, False, i))
    nodes = []
    for idx, is_split, parent in parts:
        z, y, x = idx.mean(axis=0)
        if downsample == 2:
            y, x = y * 2.0, x * 2.0  # map back to full-res coords (no refine v1)
        nodes.append((int(round(z)), int(round(y)), int(round(x)),
                      bool(is_split), int(parent)))
    nodes.sort()
    return nodes, {"pct": pct, "min_size": min_size, "max_size": max_size,
                   "thr": thr, "thr_mode": thr_mode, "k": k,
                   "downsample": downsample,
                   "n_components": int(n), "n_split": n_split,
                   "split_size": split_size, "prominence": prominence,
                   "elapsed_s": round(time.time() - t0, 2)}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("zarr")
    ap.add_argument("--t", type=int, default=0)
    ap.add_argument("--pct", type=float, default=99.5)
    ap.add_argument("--min-size", type=int, default=50)
    ap.add_argument("--thr-mode", default="percentile", choices=["percentile", "mad"],
                    help="threshold rule (EXP-0022 MAD self-calibration)")
    ap.add_argument("--k", type=float, default=12.0,
                    help="MAD multiplier (thr_mode=mad)")
    ap.add_argument("--downsample", type=int, default=1, choices=[1, 2],
                    help="2 = half-res y/x detect, map back (H-005 timing)")
    ap.add_argument("--sigma-small", default="1.0,3.0,3.0",
                    help="DoG small sigma dz,dy,dx (EXP-0014 dim-cell scale)")
    ap.add_argument("--sigma-large", default="1.6,5.0,5.0",
                    help="DoG large sigma dz,dy,dx")
    ap.add_argument("--split-size", type=int, default=None,
                    help="peak-split components larger than this (voxels)")
    ap.add_argument("--prominence", type=float, default=0.0,
                    help="secondary peaks need >= prominence * primary (EXP-0013)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import zarr
    vol = zarr.open_group(a.zarr, mode="r")["0"][a.t]
    ss = tuple(map(float, a.sigma_small.split(",")))
    sl = tuple(map(float, a.sigma_large.split(",")))
    assert len(ss) == len(sl) == 3, "--sigma-* must be dz,dy,dx"
    nodes, params = detect(vol, pct=a.pct, min_size=a.min_size,
                           sig_small=ss, sig_large=sl,
                           split_size=a.split_size, prominence=a.prominence,
                           thr_mode=a.thr_mode, k=a.k,
                           downsample=a.downsample)
    out = {"nodes": [{"id": i + 1, "t": a.t, "z": z, "y": y, "x": x,
                      "split": sp, "parent": pa}
                     for i, (z, y, x, sp, pa) in enumerate(nodes)]}
    out["params"] = params
    json.dump(out, open(a.out, "w"))
    print(f"wrote {a.out}: {len(nodes)} detections "
          f"(thr={params['thr']:.1f}, {params['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
