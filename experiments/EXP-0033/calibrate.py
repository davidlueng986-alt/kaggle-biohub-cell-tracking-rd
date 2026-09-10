#!/usr/bin/env python3
"""EXP-0033 calibrate: GT-free calibration-statistic mapping (ANALYSIS ONLY).

For each of the 6 subset samples, on window frames t=20..29, compute
candidate per-video statistics that might predict the best operating
percentile WITHOUT GT:

  (a) DoG tail-weight: frac(dog > 2*p90), frac(dog > 3*p90)
  (b) response ratios: p99/p90, p99.5/p90, p99.9/p99, (p99.5-p99)/(p99-p90)
  (c) bright-pixel counts at fixed absolute RAW levels + raw median
  (d) probe detection counts at pcts {97.5, 99.0} + ratio/difference

Ground truth (best-pct-by-recall) is ASSEMBLED from already-measured data
(EXP-0024 sweep bests + EXP-0008/0009/0011/0021 ref points) — see BEST table
below. Nothing here re-derives recall (no GT matching).

Reuse / fresh-compute accounting (cap: <=120 fresh frame-detections):
  - 60 fresh DoG responses (6 samples x 10 frames; needed for stats a/b —
    no existing artifact stores responses).
  - Probe @99.0 counts for 44b6_0113de3b + 6bba_05b6850b t20-29 (20 combos)
    are REUSED from experiments/EXP-0008 full_*_t*.json (@99.0); the fresh
    pipeline asserts thr-equality on every reused frame (fidelity gate).
  - Remaining 100 probe combos (6x10x2 - 20) are fresh threshold+label
    passes on the cached DoG (cheap; same math as scripts/dog_detect).
  - 0 full detect() calls; 1 spot-check frame vs detect() for path parity.

Test: Spearman rho of each candidate stat vs best-pct across 6 samples +
leave-one-sample-out 1-NN prediction error in pct-notch steps.
GO iff some stat has |rho| >= 0.8 AND LOO within-one-notch on >= 5/6.

CPU-only, deterministic (fixed frames/pcts, sorted iteration, no RNG).
"""
import json
import os
import sys
import time

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import numpy as np  # noqa: E402
import zarr  # noqa: E402
from scipy.ndimage import gaussian_filter, label  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from dog_detect import SIG_SMALL, SIG_LARGE  # noqa: E402 (frozen params only)

SAMPLES = ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
           "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]
T0, T1 = 20, 29
PROBES = [97.5, 99.0]
GRID = [97.5, 98.0, 98.5, 99.0, 99.5]  # pct notches for LOO error
MIN_SIZE, MAX_SIZE = 50, 50000
REUSE_PCT = 99.0
REUSE_SAMPLES = ["44b6_0113de3b", "6bba_05b6850b"]  # EXP-0008 @99.0 t20-29

assert tuple(SIG_SMALL) == (1.0, 3.0, 3.0), "frozen sigma-small drifted"
assert tuple(SIG_LARGE) == (1.6, 5.0, 5.0), "frozen sigma-large drifted"

# best-pct-by-recall ASSEMBLED from already-measured data (no re-derivation).
# provenance: exact artifact + tie-break rule per sample.
BEST = {
    # EXP-0008 full-video rec 1.00 @99.0 AND EXP-0009 rec 1.00 @98.5 (tie) ->
    # fewer-dets rule (det/f 140.1 < 188.4) -> 99.0. Censored below 98.5.
    "44b6_0113de3b": {"pct": 99.0, "recall": 1.00,
                      "prov": "EXP-0008/0009 tie 1.00@99.0+98.5, fewer-dets"},
    # EXP-0024 sweep rec 0.80 @97.5/98.0/98.5 (tie) -> fewest dets -> 98.5.
    "44b6_0b24845f": {"pct": 98.5, "recall": 0.80,
                      "prov": "EXP-0024 sweep tie 0.80, fewer-dets"},
    # EXP-0024 sweep strictly best 0.50 @97.5 (next 0.10 @98.0).
    "44b6_0c582fdc": {"pct": 97.5, "recall": 0.50,
                      "prov": "EXP-0024 sweep strict best"},
    # Full-video rec 0.893 @98.5 (EXP-0009) > 0.880 @98.0 (EXP-0011) >
    # 0.835 @99.0 (EXP-0008). Never swept @97.5 (censored low side).
    "6bba_05b6850b": {"pct": 98.5, "recall": 0.893,
                      "prov": "EXP-0008/0009/0011 three-point best"},
    # EXP-0024 sweep strictly best 0.4056 @97.5, monotone decreasing w/ pct.
    "6bba_05db0fb1": {"pct": 97.5, "recall": 0.4056,
                      "prov": "EXP-0024 sweep strict best"},
    # EXP-0021 single-point 0.93 @98.5 (per-embryo level). Never swept
    # (fully censored) — weakest GT row, flagged in notes.md.
    "6bba_062c8d37": {"pct": 98.5, "recall": 0.93,
                      "prov": "EXP-0021 single point (censored)"},
}

STAT_ORDER = ["tail2x", "tail3x", "r99_90", "r995_90", "r999_99",
              "slope_ratio", "bright1000", "bright1500", "rawmed",
              "n975", "n990", "nratio", "ndiff", "thr975", "thr990"]


def frame_stats(vol):
    """One fresh DoG + all response stats + both probe thresholds/labels."""
    v = np.asarray(vol, dtype=np.float32)
    dog = (gaussian_filter(v, SIG_SMALL) - gaussian_filter(v, SIG_LARGE))
    p = np.percentile(dog, [50, 90, 95, 97.5, 98, 98.5, 99, 99.5, 99.9])
    p50, p90, p95, p975, p98, p985, p99, p995, p999 = (float(q) for q in p)
    out = {}
    out["tail2x"] = float(np.mean(dog > 2.0 * p90))
    out["tail3x"] = float(np.mean(dog > 3.0 * p90))
    out["r99_90"] = p99 / p90 if p90 > 1e-9 else float("nan")
    out["r995_90"] = p995 / p90 if p90 > 1e-9 else float("nan")
    out["r999_99"] = p999 / p99 if p99 > 1e-9 else float("nan")
    out["slope_ratio"] = ((p995 - p99) / (p99 - p90)
                          if (p99 - p90) > 1e-9 else float("nan"))
    out["bright1000"] = float(np.mean(v > 1000))
    out["bright1500"] = float(np.mean(v > 1500))
    out["rawmed"] = float(np.median(v))
    out["thr975"], out["thr990"] = p975, p99
    out["_dog"] = dog  # cached for probe labels (not serialized)
    return out


def count_at(dog, thr):
    """Replicates scripts/dog_detect count path (label + size filter)."""
    bw = dog >= thr
    lab, n = label(bw)
    if n == 0:
        return 0
    sizes = np.bincount(lab.ravel())
    return int(sum(1 for i in range(1, n + 1)
                   if MIN_SIZE <= int(sizes[i]) <= MAX_SIZE))


def main():
    t_start = time.time()
    fresh_dog = 0
    fresh_labels = 0
    reused = 0
    per_frame = {s: [] for s in SAMPLES}

    for sid in SAMPLES:
        group = zarr.open_group(os.path.join(ROOT, "data/train", f"{sid}.zarr"),
                                mode="r")["0"]
        for t in range(T0, T1 + 1):
            st = frame_stats(group[t])
            fresh_dog += 1
            dog = st.pop("_dog")
            # probe @97.5: always fresh
            st["n975"] = count_at(dog, st["thr975"])
            fresh_labels += 1
            # probe @99.0: reuse EXP-0008 file where covered, else fresh
            if sid in REUSE_SAMPLES:
                f = json.load(open(os.path.join(
                    ROOT, "experiments/EXP-0008",
                    f"full_{sid}_t{t}.json")))
                fpct = f["params"]["pct"]
                assert abs(fpct - REUSE_PCT) < 1e-9, f"reuse pct drift {fpct}"
                fthr = float(f["params"]["thr"])
                # fidelity gate: fresh thr must match archived thr to 1e-4
                # (float32 filter/percentile noise floor is ~1e-6; thresholds
                #  are O(50-250) so 1e-4 is far below decision scale).
                assert abs(st["thr990"] - fthr) / max(abs(fthr), 1e-9) < 1e-4, (
                    f"thr mismatch {sid} t{t}: {st['thr990']} vs {fthr}")
                st["n990"] = len(f["nodes"])
                reused += 1
            else:
                st["n990"] = count_at(dog, st["thr990"])
                fresh_labels += 1
            st["nratio"] = st["n975"] / max(st["n990"], 1)
            st["ndiff"] = st["n975"] - st["n990"]
            per_frame[sid].append(st)

    assert fresh_dog <= 120, f"cap breach: {fresh_dog} fresh DoGs"

    # spot-check: fresh label path vs scripts/dog_detect.detect on 1 frame
    from dog_detect import detect as _detect
    _vol = zarr.open_group(os.path.join(
        ROOT, "data/train", "6bba_05b6850b.zarr"), mode="r")["0"][20]
    _nodes, _ = _detect(_vol, pct=97.5, min_size=MIN_SIZE,
                        sig_small=tuple(SIG_SMALL),
                        sig_large=tuple(SIG_LARGE))
    _mine = per_frame["6bba_05b6850b"][0]["n975"]
    assert len(_nodes) == _mine, (f"path parity fail: detect={len(_nodes)} "
                                  f"mine={_mine}")
    path_parity = {"sample": "6bba_05b6850b", "t": 20, "pct": 97.5,
                   "detect_count": len(_nodes), "mine": _mine, "match": True}

    # per-video stat = median over window frames
    table = {}
    for sid in SAMPLES:
        table[sid] = {}
        for k in STAT_ORDER:
            vals = [fr[k] for fr in per_frame[sid]]
            table[sid][k] = float(np.median(vals))
        table[sid]["best_pct"] = BEST[sid]["pct"]

    # rank-correlation per stat vs best-pct + LOO 1-NN notch error
    y = np.array([BEST[s]["pct"] for s in SAMPLES])
    results = {}
    for k in STAT_ORDER:
        x = np.array([table[s][k] for s in SAMPLES])
        assert np.all(np.isfinite(x)), f"non-finite stat {k}: {x}"
        rho, pval = spearmanr(x, y)
        # LOO: 1-NN in stat space on other 5 -> predict best-pct notch
        errs, hits = [], []
        for i, sid in enumerate(SAMPLES):
            xo = np.delete(x, i)
            yo = np.delete(y, i)
            d = np.abs(xo - x[i])
            m = d.min()
            cand = sorted(set(float(v) for v, dd in zip(yo, d) if dd == m),
                          reverse=True)  # tie -> higher pct (fewer-dets rule)
            pred = cand[0]
            err = abs(GRID.index(pred) - GRID.index(float(y[i])))
            errs.append(err)
            hits.append(err <= 1)
        results[k] = {"rho": round(float(rho), 4),
                      "p_two_sided": round(float(pval), 4),
                      "loo_err_notches": errs,
                      "loo_mean_err": round(float(np.mean(errs)), 3),
                      "loo_within1": f"{sum(hits)}/6"}

    go_stats = [k for k, r in results.items()
                if abs(r["rho"]) >= 0.8
                and sum(e <= 1 for e in r["loo_err_notches"]) >= 5]
    verdict = ("GO" if go_stats else "STOP")
    best_stat = (max(results, key=lambda k: (abs(results[k]["rho"]), k))
                 if results else None)

    metrics = {
        "exp_id": "EXP-0033",
        "title": "Calibration-statistic mapping",
        "status": "done",
        "protocol_version": "1.1",
        "real_data": True,
        "image_based": True,
        "simplified_scorer": False,
        "scope": ("analysis-only: GT-free stat vs assembled best-pct; "
                  "no new detection policy, no edges"),
        "window": {"t0": T0, "t1": T1, "n_frames": T1 - T0 + 1},
        "detector": {"sig_small": list(SIG_SMALL),
                     "sig_large": list(SIG_LARGE), "min_size": MIN_SIZE,
                     "thr_mode": "percentile"},
        "compute": {"fresh_dog_frames": fresh_dog,
                    "fresh_probe_labels": fresh_labels,
                    "reused_probe_counts": reused,
                    "cap": 120, "within_cap": fresh_dog <= 120,
                    "path_parity_vs_dog_detect": path_parity,
                    "reuse_source": "experiments/EXP-0008/full_<sid>_t*.json"},
        "best_pct_gt": {s: BEST[s] for s in SAMPLES},
        "stat_table_median_over_window": {s: table[s] for s in SAMPLES},
        "rank_test": results,
        "criterion": ("|rho|>=0.8 AND LOO within-one-notch >=5/6 "
                      "(notches [97.5,98,98.5,99,99.5])"),
        "go_stats": go_stats,
        "best_stat": best_stat,
        "verdict": verdict,
        "wall_s": round(time.time() - t_start, 1),
    }
    with open(os.path.join(EXP_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    b = results[best_stat]
    print(f"[EXP-0033] best={best_stat} rho={b['rho']} p={b['p_two_sided']} "
          f"LOOwithin1={b['loo_within1']} mean_err={b['loo_mean_err']}")
    print(f"[EXP-0033] verdict={verdict} go_stats={go_stats} "
          f"({metrics['wall_s']}s wall; fresh DoG {fresh_dog}/120)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
