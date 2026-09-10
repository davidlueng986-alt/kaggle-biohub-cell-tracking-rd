#!/usr/bin/env python3
"""EXP-0027 detection-internals profile (ANALYSIS ONLY, CPU-only, deterministic).

Times EACH stage inside scripts/dog_detect.detect() separately on 10 frames
(2 videos x t=20..24) with mission parameters pct=98.5, min_size=50,
split_size=None (no split):

  cast, gauss_small, gauss_large, subtract, percentile, label,
  bincount, moments_means, split_skipped(=0.0, recorded for completeness)

Fidelity: imports SIG_SMALL/SIG_LARGE from scripts/dog_detect (read-only
import; scripts/ never modified) and replicates the exact scipy/numpy calls
with perf_counter timers. Per frame, also runs DD.detect() whole (untimed
warmup + timed cross-check) and asserts staged replication yields identical
node count and threshold.

Reads zarr frames only (arr[t] views); never copies/writes data stores.

Usage: python3 experiments/EXP-0027/profile_detect.py [--out metrics.json]
Writes: experiments/EXP-0027/metrics.json
"""

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dog_detect as DD  # noqa: E402  (read-only import; never modified)

from scipy.ndimage import gaussian_filter, label  # noqa: E402

EXP_DIR = os.path.join(ROOT, "experiments", "EXP-0027")

PCT = 98.5
MIN_SIZE = 50
MAX_SIZE = 50000
SPLIT_SIZE = None  # off -> split_skipped stage records 0.0

VIDEOS = [
    ("dense_6bba_05b6850b", "data/train/6bba_05b6850b.zarr"),
    ("sparse_44b6_0113de3b", "data/train/44b6_0113de3b.zarr"),
]
TIMES = [20, 21, 22, 23, 24]

STAGES = ["cast", "gauss_small", "gauss_large", "subtract", "percentile",
          "label", "bincount", "moments_means", "split_skipped"]


def stage_profile(vol):
    """Replicate DD.detect() body with per-stage perf_counter timers."""
    t = {}
    s = time.perf_counter()
    v = np.asarray(vol, dtype=np.float32)
    t["cast"] = time.perf_counter() - s

    s = time.perf_counter()
    g_small = gaussian_filter(v, DD.SIG_SMALL)
    t["gauss_small"] = time.perf_counter() - s

    s = time.perf_counter()
    g_large = gaussian_filter(v, DD.SIG_LARGE)
    t["gauss_large"] = time.perf_counter() - s

    s = time.perf_counter()
    dog = g_small - g_large
    del g_small, g_large
    t["subtract"] = time.perf_counter() - s

    s = time.perf_counter()
    thr = float(np.percentile(dog, PCT))
    t["percentile"] = time.perf_counter() - s

    s = time.perf_counter()
    bw = dog >= thr
    lab, n = label(bw)
    del bw
    t["label"] = time.perf_counter() - s

    s = time.perf_counter()
    sizes = np.bincount(lab.ravel())
    t["bincount"] = time.perf_counter() - s

    s = time.perf_counter()
    parts = []
    for i in range(1, n + 1):
        si = int(sizes[i])
        if not (MIN_SIZE <= si <= MAX_SIZE):
            continue
        idx = np.argwhere(lab == i)
        parts.append((idx, False, i))
    nodes = []
    for idx, is_split, parent in parts:
        z, y, x = idx.mean(axis=0)
        nodes.append((int(round(z)), int(round(y)), int(round(x)),
                      bool(is_split), int(parent)))
    nodes.sort()
    t["moments_means"] = time.perf_counter() - s

    t["split_skipped"] = 0.0  # SPLIT_SIZE=None: no peak-split work
    t["staged_total"] = sum(t[k] for k in STAGES)
    return t, nodes, thr, int(n), len(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(EXP_DIR, "metrics.json"))
    a = ap.parse_args()

    import zarr

    # Warmup (import/first-call overhead outside timed region).
    warm = np.asarray(
        zarr.open_group(os.path.join(ROOT, VIDEOS[0][1]), mode="r")["0"][20],
        dtype=np.float32,
    )
    gaussian_filter(warm, DD.SIG_SMALL)
    del warm

    videos = []
    for tag, rel in VIDEOS:
        arr = zarr.open_group(os.path.join(ROOT, rel), mode="r")["0"]
        frames = []
        for tt in TIMES:
            vol = arr[tt]  # read-only frame read
            staged_t, staged_nodes, thr, n_comp, n_kept = stage_profile(vol)
            # Whole-function cross-check (fidelity gate).
            w0 = time.perf_counter()
            ref_nodes, ref_params = DD.detect(vol, pct=PCT, min_size=MIN_SIZE,
                                              split_size=SPLIT_SIZE)
            whole_s = time.perf_counter() - w0
            assert len(staged_nodes) == len(ref_nodes), \
                f"{tag} t={tt}: staged {len(staged_nodes)} != detect() {len(ref_nodes)}"
            assert staged_nodes == [(z, y, x, sp, pa) for (z, y, x, sp, pa) in ref_nodes], \
                f"{tag} t={tt}: staged nodes differ from detect()"
            assert abs(thr - float(ref_params["thr"])) < 1e-3, \
                f"{tag} t={tt}: thr {thr} != {ref_params['thr']}"
            staged_t["detect_whole_s"] = whole_s
            staged_t["residual_s"] = whole_s - staged_t["staged_total"]
            frames.append({
                "t": tt, "stage_s": {k: staged_t[k] for k in STAGES},
                "staged_total_s": staged_t["staged_total"],
                "detect_whole_s": whole_s,
                "residual_s": staged_t["residual_s"],
                "n_components": n_comp, "n_kept": n_kept,
                "n_nodes": len(ref_nodes), "thr": thr,
            })
            print(f"[{tag} t={tt}] staged={staged_t['staged_total']:.2f}s "
                  f"whole={whole_s:.2f}s nodes={len(ref_nodes)} "
                  f"gS={staged_t['gauss_small']:.2f}s gL={staged_t['gauss_large']:.2f}s "
                  f"pct={staged_t['percentile']:.2f}s lab={staged_t['label']:.2f}s",
                  flush=True)
        mean = {k: float(np.mean([f["stage_s"][k] for f in frames])) for k in STAGES}
        tot = float(sum(mean.values()))
        videos.append({
            "tag": tag, "zarr": rel, "pct": PCT, "min_size": MIN_SIZE,
            "split_size": SPLIT_SIZE, "frames": frames,
            "mean_stage_s": mean,
            "mean_staged_total_s": tot,
            "mean_detect_whole_s": float(np.mean([f["detect_whole_s"] for f in frames])),
            "share": {k: (mean[k] / tot if tot > 0 else 0.0) for k in STAGES},
        })

    # Top-paydown projection (computed from measured shares; implements nothing).
    # Candidate V (top): vectorized centroids — replace the per-component
    #   np.argwhere(lab == i) loop (one full-volume scan per kept component,
    #   measured ~10ms/scan, linear in C) with single-pass bincount/
    #   center_of_mass centroid computation. Cost model from measured
    #   full-volume pass costs (bincount pass ~0.03s, coord-sum passes heavier):
    #   conservative VEC_COST_S=0.12s/frame for the whole moments stage.
    # Candidate A: footprint-truncated gaussians (truncate 4.0 -> 2.0).
    #   Separable cost ~= sum(kernel widths); widths scale ~linearly with
    #   truncate -> each gauss ~2x faster (conservative: 45% off each).
    # Candidate B: percentile subsampling stride 8 (~7/8 off percentile).
    # Candidate C: drop large-gauss (single-scale) — quality risk, listed only.
    VEC_COST_S = 0.12
    proj = {}
    for v in videos:
        sh, ms = v["share"], v["mean_stage_s"]
        gauss = ms["gauss_small"] + ms["gauss_large"]
        save_trunc = 0.45 * gauss
        save_pct = 0.875 * ms["percentile"]
        save_vec = max(0.0, ms["moments_means"] - VEC_COST_S)
        tot = v["mean_staged_total_s"]
        proj[v["tag"]] = {
            "vectorized_moments_s_per_frame": save_vec,
            "vectorized_moments_share_of_frame": save_vec / tot,
            "truncate_gauss_4to2_s_per_frame": save_trunc,
            "truncate_gauss_4to2_share_of_frame": save_trunc / tot,
            "percentile_subsample_x8_s_per_frame": save_pct,
            "percentile_subsample_x8_share_of_frame": save_pct / tot,
            "drop_large_gauss_s_per_frame": ms["gauss_large"],
            "drop_large_gauss_share_of_frame": sh["gauss_large"],
        }
    dense, sparse = videos[0]["tag"], videos[1]["tag"]
    cands = ["vectorized_moments", "truncate_gauss_4to2",
             "percentile_subsample_x8", "drop_large_gauss"]
    top = max(cands, key=lambda c: (proj[dense][c + "_s_per_frame"]
                                    + proj[sparse][c + "_s_per_frame"]))

    metrics = {
        "exp_id": "EXP-0027",
        "title": "Detection-internals profile",
        "status": "done",
        "method": ("per-stage perf_counter replication of DD.detect() exact calls "
                   "(gaussian_filter SIG_SMALL/SIG_LARGE defaults, percentile, "
                   "label, bincount, argwhere+mean loops); split_size=None so "
                   "split_skipped=0.0; fidelity gate: staged nodes==detect() "
                   "nodes and thr match every frame; scripts/dog_detect.py unmodified"),
        "params": {"pct": PCT, "min_size": MIN_SIZE, "max_size": MAX_SIZE,
                   "split_size": SPLIT_SIZE, "sig_small": list(DD.SIG_SMALL),
                   "sig_large": list(DD.SIG_LARGE),
                   "note": "mission pct=98.5 used; CLI --pct default in "
                           "dog_detect.py is 99.5 (discrepancy noted in notes.md)"},
        "videos": videos,
        "projections": proj,
        "top_recommendation": {
            "id": top,
            "dense_saving_per_frame_s": proj[dense][top + "_s_per_frame"],
            "dense_saving_share": proj[dense][top + "_share_of_frame"],
            "sparse_saving_per_frame_s": proj[sparse][top + "_s_per_frame"],
            "sparse_saving_share": proj[sparse][top + "_share_of_frame"],
        },
        "fidelity": "all 10 frames: staged node list identical to DD.detect(), thr match <1e-3",
    }
    json.dump(metrics, open(a.out, "w"), indent=2)
    print(f"[EXP-0027] wrote {a.out} top={top}")


if __name__ == "__main__":
    main()
