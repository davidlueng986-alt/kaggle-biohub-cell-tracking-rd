#!/usr/bin/env python3
"""ROI-masked DoG detection wrapper (EXP-0026, CPU-only, deterministic).

Uses scripts/dog_detect.detect UNMODIFIED for per-ROI full-res DoG; this
module only builds a cheap foreground mask and crops/offsets coordinates.

Mask: strided half-res intensity vol[:, ::2, ::2] (no interpolation cost),
adaptive percentile threshold (q, default 98), scipy connected labeling on
the half-res mask, one processing box per component via find_objects
(O(mask) total, no per-component full scans). Boxes are mapped to full-res
coords (x2 in y/x) and expanded by a halo margin (z/y/x) that doubles as
Gaussian context so interior DoG matches full-frame response.

Per box: detect(crop, pct, min_size) at FULL resolution, centroids offset
back to full-frame coords, pooled across boxes, exact-deduplicated
(sorted set). NOTE (known limitation, measured in notes.md): the pct
percentile threshold is evaluated PER BOX, not globally, so box thresholds
differ from the full-frame threshold in both directions (misses inside
bright boxes, extras inside dim boxes). No absolute-threshold injection is
possible without editing dog_detect.py (out of scope).

Usage:
  python3 experiments/EXP-0026/roi_detect.py data/train/SID.zarr --t 20 \
      --out experiments/EXP-0026/ROI_t20.json
  python3 experiments/EXP-0026/roi_detect.py data/train/SID.zarr --t 20 \
      --q 95 --pct 98.5 --out ROI_t20_q95.json

Output: {"nodes":[{id,t,z,y,x}...], "params":{... mask_s, det_s, nbox,
vox_frac, q, halo, pct, min_size, elapsed_s}}
"""
import json
import sys
import time

sys.path.insert(0, __import__("os").path.join(
    __import__("os").path.dirname(__import__("os").path.abspath(__file__)),
    "..", "..", "scripts"))
from dog_detect import detect  # noqa: E402  (frozen detector, unmodified)


def roi_detect(vol, q=98.0, pct=98.5, min_size=50,
               halo=(6, 16, 16)):
    """Returns (nodes, params). nodes: sorted unique (z,y,x) int tuples."""
    import numpy as np
    from scipy.ndimage import label, find_objects
    t0 = time.time()
    v = np.asarray(vol)
    Z, Y, X = v.shape
    mz, my, mx = halo
    # --- cheap foreground mask on strided half-res (y/x) ---
    small = v[:, ::2, ::2]
    thr = float(np.percentile(small, q))
    bw = small >= thr
    lab, nbox = label(bw)
    t_mask = time.time() - t0
    # --- boxes via find_objects (single pass), mapped x2 + halo ---
    boxes = []
    vox_proc = 0
    for sl in find_objects(lab):
        if sl is None:
            continue
        sz, sy, sx = sl
        zlo = max(0, sz.start - mz)
        zhi = min(Z, sz.stop + mz)
        ylo = max(0, sy.start * 2 - my)
        yhi = min(Y, sy.stop * 2 + my)
        xlo = max(0, sx.start * 2 - mx)
        xhi = min(X, sx.stop * 2 + mx)
        boxes.append((zlo, zhi, ylo, yhi, xlo, xhi))
        vox_proc += (zhi - zlo) * (yhi - ylo) * (xhi - xlo)
    boxes.sort()
    # --- full-res DoG per box via frozen detect() ---
    t_det0 = time.time()
    det_s = 0.0
    out = []
    for (zlo, zhi, ylo, yhi, xlo, xhi) in boxes:
        crop = np.asarray(v[zlo:zhi, ylo:yhi, xlo:xhi])
        nodes, params = detect(crop, pct=pct, min_size=min_size)
        det_s += params["elapsed_s"]
        for (z, y, x, _sp, _pa) in nodes:
            gz, gy, gx = z + zlo, y + ylo, x + xlo
            if 0 <= gz < Z and 0 <= gy < Y and 0 <= gx < X:
                out.append((gz, gy, gx))
    t_det = time.time() - t_det0
    out = sorted(set(out))
    elapsed = time.time() - t0
    params = {"q": q, "mask_thr": thr, "pct": pct, "min_size": min_size,
              "halo": list(halo), "nbox": int(nbox),
              "vox_frac": round(vox_proc / v.size, 4),
              "mask_s": round(t_mask, 3), "det_s": round(det_s, 3),
              "loop_s": round(t_det, 3), "elapsed_s": round(elapsed, 3)}
    return out, params


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("zarr")
    ap.add_argument("--t", type=int, default=0)
    ap.add_argument("--q", type=float, default=98.0)
    ap.add_argument("--pct", type=float, default=98.5)
    ap.add_argument("--min-size", type=int, default=50)
    ap.add_argument("--halo", default="6,16,16")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import zarr
    vol = zarr.open_group(a.zarr, mode="r")["0"][a.t]
    halo = tuple(int(x) for x in a.halo.split(","))
    assert len(halo) == 3
    nodes, params = roi_detect(vol, q=a.q, pct=a.pct,
                               min_size=a.min_size, halo=halo)
    out = {"nodes": [{"id": i + 1, "t": a.t, "z": z, "y": y, "x": x}
                     for i, (z, y, x) in enumerate(nodes)]}
    out["params"] = params
    json.dump(out, open(a.out, "w"))
    print(f"wrote {a.out}: {len(nodes)} detections "
          f"(q={a.q} mask_thr={params['mask_thr']:.0f} nbox={params['nbox']} "
          f"vox_frac={params['vox_frac']} {params['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
