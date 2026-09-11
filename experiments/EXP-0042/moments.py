#!/usr/bin/env python3
"""EXP-0042 higher-moment DoG shape descriptors (ANALYSIS ONLY).

For each of the 6 subset samples, on window frames t=20..29, compute
GT-free higher-moment shape descriptors of the frozen-DoG response:

  (a) skew    — population skewness of the DoG voxel distribution
  (b) kurt_x  — population excess kurtosis of the DoG voxel distribution
  (c) tail6/12/24 — frac(DoG > median + k*MAD), k in {6, 12, 24}
      (level-free fraction version of EXP-0022's failed absolute MAD rule)
  (d) r995_50 — p99.5/p50 ratio (note: DoG p50 < 0 on all frames, so the
      ratio is negative; |rho| is sign-invariant, ranking = reverse of
      p99.5/|p50|)
  (e) otsu_frac — frac(DoG > Otsu threshold of the 256-bin DoG histogram)

Ground truth per sample = fixed-@98.5 window recall (matched/total GT via
score.match_nodes over t20-29) + assembled best-pct (EXP-0033 assembly).
@98.5 det sources: EXP-0009 (0113de3b, 05b6850b), EXP-0021 (05db0fb1,
062c8d37), fresh run.sh detects in this dir (0b24845f, 0c582fdc).

Test: Spearman rho of each stat vs fixed-@98.5 recall AND vs best-pct +
leave-one-sample-out 1-NN notch error vs best-pct (EXP-0033 procedure).
GO iff some stat has |rho| >= 0.8 on either target AND LOO within-one-notch
on >= 5/6. Else STOP.

CPU-only, deterministic (fixed frames, sorted iteration, no RNG).
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
from scipy.ndimage import gaussian_filter  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from dog_detect import SIG_SMALL, SIG_LARGE  # noqa: E402 (frozen params only)
from score import match_nodes  # noqa: E402 (recall readout only)

SAMPLES = ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
           "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]
T0, T1 = 20, 29
GRID = [97.5, 98.0, 98.5, 99.0, 99.5]  # pct notches for LOO error
REF_PCT = 98.5
MIN_SIZE = 50
FRESH_CAP_STEP = 30
FRESH_CAP_GLOBAL = 60

assert tuple(SIG_SMALL) == (1.0, 3.0, 3.0), "frozen sigma-small drifted"
assert tuple(SIG_LARGE) == (1.6, 5.0, 5.0), "frozen sigma-large drifted"

# best-pct-by-recall ASSEMBLED from already-measured data (EXP-0033 assembly;
# no re-derivation here). 05db0fb1 primary 97.5 = EXP-0024 sweep floor;
# sensitivity alt 96.0 recorded (mission prior-art note "97.5/96.0-window").
BEST = {
    "44b6_0113de3b": {"pct": 99.0, "prov": "EXP-0008/0009 tie 1.00@99.0+98.5"},
    "44b6_0b24845f": {"pct": 98.5, "prov": "EXP-0024 sweep tie 0.80"},
    "44b6_0c582fdc": {"pct": 97.5, "prov": "EXP-0024 sweep strict best"},
    "6bba_05b6850b": {"pct": 98.5, "prov": "EXP-0008/0009/0011 three-point"},
    "6bba_05db0fb1": {"pct": 97.5, "prov": "EXP-0024 sweep strict best"},
    "6bba_062c8d37": {"pct": 98.5, "prov": "EXP-0021 single point"},
}
BEST_ALT = dict(BEST)
BEST_ALT["6bba_05db0fb1"] = {"pct": 96.0, "prov": "sensitivity alt"}

# @98.5 det sources for window t20-29 (verified present by ls before run).
REUSE = {
    "44b6_0113de3b": "experiments/EXP-0009/full_44b6_0113de3b_t{t}.json",
    "44b6_0b24845f": None,  # fresh: det98_44b6_0b24845f_t{t}.json (this dir)
    "44b6_0c582fdc": None,  # fresh: det98_44b6_0c582fdc_t{t}.json (this dir)
    "6bba_05b6850b": "experiments/EXP-0009/full_6bba_05b6850b_t{t}.json",
    "6bba_05db0fb1": "experiments/EXP-0021/full_6bba_05db0fb1_t{t}.json",
    "6bba_062c8d37": "experiments/EXP-0021/full_6bba_062c8d37_t{t}.json",
}

STAT_ORDER = ["skew", "kurt_x", "tail6", "tail12", "tail24",
              "r995_50", "otsu_frac"]


def otsu_threshold(x, nbins=256):
    """Otsu threshold of a float array via histogram (deterministic)."""
    lo, hi = float(x.min()), float(x.max())
    assert hi > lo, "degenerate constant array"
    hist, edges = np.histogram(x, bins=nbins, range=(lo, hi))
    hist = hist.astype(np.float64)
    total = hist.sum()
    centers = (edges[:-1] + edges[1:]) / 2.0
    w1 = np.cumsum(hist) / total
    mu1 = np.cumsum(hist * centers) / total
    mu = mu1[-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        between = (mu * w1 - mu1) ** 2 / np.maximum(w1 * (1.0 - w1), 1e-300)
    between[(w1 <= 0) | (w1 >= 1)] = -1.0
    return float(centers[int(np.argmax(between))])


def frame_stats(vol):
    """One fresh DoG + all higher-moment shape descriptors."""
    v = np.asarray(vol, dtype=np.float32)
    dog = (gaussian_filter(v, tuple(SIG_SMALL))
           - gaussian_filter(v, tuple(SIG_LARGE)))
    x = dog.ravel().astype(np.float64)
    mu = x.mean()
    xc = x - mu
    m2 = np.mean(xc ** 2)
    assert m2 > 0, "degenerate zero-variance DoG"
    m3 = np.mean(xc ** 3)
    m4 = np.mean(xc ** 4)
    out = {}
    out["skew"] = float(m3 / m2 ** 1.5)
    out["kurt_x"] = float(m4 / m2 ** 2 - 3.0)
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) + 1e-9
    out["med"] = med
    out["mad"] = mad
    for k in (6, 12, 24):
        out[f"tail{k}"] = float(np.mean(x > med + k * mad))
    p50, p995 = (float(q) for q in np.percentile(x, [50, 99.5]))
    out["r995_50"] = (p995 / p50 if abs(p50) > 1e-9 else float("nan"))
    out["otsu_frac"] = float(np.mean(x > otsu_threshold(x)))
    return out


def window_recall(sid):
    """Fixed-@98.5 window recall from reuse/fresh det files + EXP-0003 GT."""
    gt = json.load(open(os.path.join(
        ROOT, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    rec_n = rec_d = 0
    n_det = 0
    for t in range(T0, T1 + 1):
        src = REUSE[sid]
        path = os.path.join(EXP_DIR, f"det98_{sid}_t{t}.json") if src is None \
            else os.path.join(ROOT, src.format(t=t))
        d = json.load(open(path))
        p = d.get("params", {})
        assert abs(float(p.get("pct", -1)) - REF_PCT) < 1e-9, \
            f"reuse pct drift {sid} t{t}: {p.get('pct')}"
        assert int(p.get("min_size", -1)) == MIN_SIZE, \
            f"reuse min_size drift {sid} t{t}"
        g = [n for n in gt["nodes"] if n["t"] == t]
        _, g2p = match_nodes(d["nodes"], g)
        rec_n += len(g2p)
        rec_d += len(g)
        n_det += len(d["nodes"])
    return rec_n / rec_d if rec_d else float("nan"), rec_n, rec_d, n_det


def main():
    t_start = time.time()
    fresh_requested = sum(1 for s in SAMPLES if REUSE[s] is None) * (T1 - T0 + 1)
    assert fresh_requested <= FRESH_CAP_STEP, f"step cap breach: {fresh_requested}"
    assert fresh_requested <= FRESH_CAP_GLOBAL, "global cap breach"

    per_frame = {s: [] for s in SAMPLES}
    fresh_dog = 0
    group_cache = {}
    for sid in SAMPLES:
        group_cache[sid] = zarr.open_group(
            os.path.join(ROOT, "data/train", f"{sid}.zarr"), mode="r")["0"]
    for sid in SAMPLES:
        for t in range(T0, T1 + 1):
            per_frame[sid].append(frame_stats(group_cache[sid][t]))
            fresh_dog += 1

    # fixed-@98.5 recall ground truth (+ cross-checks vs EXP-0024 sweep means)
    recall, rec_detail = {}, {}
    for sid in SAMPLES:
        r, n, d, ndet = window_recall(sid)
        recall[sid] = r
        rec_detail[sid] = {"recall98": round(r, 4), "matched": n,
                           "gt_total": d, "n_det": ndet}
    checks = {"6bba_05db0fb1": 0.1888, "44b6_0b24845f": 0.80,
              "44b6_0c582fdc": 0.00}
    for sid, exp in checks.items():
        assert abs(recall[sid] - exp) < 0.02, \
            f"recall cross-check fail {sid}: {recall[sid]} vs {exp}"

    # per-video stat = median over window frames
    table = {}
    for sid in SAMPLES:
        table[sid] = {}
        for k in STAT_ORDER + ["med", "mad"]:
            table[sid][k] = float(np.median([fr[k] for fr in per_frame[sid]]))
        table[sid]["recall98"] = recall[sid]
        table[sid]["best_pct"] = BEST[sid]["pct"]

    y_best = np.array([BEST[s]["pct"] for s in SAMPLES])
    y_rec = np.array([recall[s] for s in SAMPLES])
    y_alt = np.array([BEST_ALT[s]["pct"] for s in SAMPLES])
    results = {}
    for k in STAT_ORDER:
        x = np.array([table[s][k] for s in SAMPLES])
        assert np.all(np.isfinite(x)), f"non-finite stat {k}: {x}"
        rho_b, pb = spearmanr(x, y_best)
        rho_r, pr = spearmanr(x, y_rec)
        rho_a, _ = spearmanr(x, y_alt)
        errs, hits = [], []
        for i, sid in enumerate(SAMPLES):
            xo = np.delete(x, i)
            yo = np.delete(y_best, i)
            d = np.abs(xo - x[i])
            m = d.min()
            cand = sorted(set(float(v) for v, dd in zip(yo, d) if dd == m),
                          reverse=True)  # tie -> higher pct (fewer-dets rule)
            pred = cand[0]
            err = abs(GRID.index(pred) - GRID.index(float(y_best[i])))
            errs.append(err)
            hits.append(err <= 1)
        results[k] = {"rho_best": round(float(rho_b), 4),
                      "p_best": round(float(pb), 4),
                      "rho_fixed98": round(float(rho_r), 4),
                      "p_fixed98": round(float(pr), 4),
                      "rho_best_alt96": round(float(rho_a), 4),
                      "loo_err_notches": errs,
                      "loo_mean_err": round(float(np.mean(errs)), 3),
                      "loo_within1": f"{sum(hits)}/6"}

    go_stats = [k for k, r in results.items()
                if (abs(r["rho_best"]) >= 0.8 or abs(r["rho_fixed98"]) >= 0.8)
                and sum(e <= 1 for e in r["loo_err_notches"]) >= 5]
    verdict = "GO" if go_stats else "STOP"
    best_stat = max(results,
                    key=lambda k: (max(abs(results[k]["rho_best"]),
                                       abs(results[k]["rho_fixed98"])), k))

    metrics = {
        "exp_id": "EXP-0042",
        "title": "Higher-moment DoG shape descriptors vs operating level",
        "status": "done",
        "protocol_version": "1.1",
        "real_data": True,
        "image_based": True,
        "simplified_scorer": False,
        "scope": ("analysis-only: GT-free higher-moment stat vs fixed-@98.5 "
                  "recall + assembled best-pct; no new detection policy"),
        "window": {"t0": T0, "t1": T1, "n_frames": T1 - T0 + 1},
        "detector": {"sig_small": list(SIG_SMALL),
                     "sig_large": list(SIG_LARGE), "min_size": MIN_SIZE,
                     "thr_mode": "percentile", "ref_pct": REF_PCT},
        "compute": {"fresh_dog_frames": fresh_dog,
                    "fresh_detect_frames": fresh_requested,
                    "fresh_sources": sorted(s for s in SAMPLES
                                            if REUSE[s] is None),
                    "reuse_sources": {s: REUSE[s] for s in SAMPLES
                                      if REUSE[s] is not None},
                    "step_cap": FRESH_CAP_STEP, "global_cap": FRESH_CAP_GLOBAL,
                    "within_cap": fresh_requested <= FRESH_CAP_STEP},
        "recall98_gt": rec_detail,
        "best_pct_gt": {s: BEST[s] for s in SAMPLES},
        "best_pct_sensitivity_alt": {s: BEST_ALT[s] for s in SAMPLES},
        "stat_table_median_over_window": {s: table[s] for s in SAMPLES},
        "rank_test": results,
        "criterion": ("|rho|>=0.8 (vs best-pct OR fixed-@98.5 recall) AND "
                      "LOO within-one-notch >=5/6 (notches [97.5,98,98.5,99,99.5])"),
        "go_stats": go_stats,
        "best_stat": best_stat,
        "verdict": verdict,
        "wall_s": round(time.time() - t_start, 1),
    }
    with open(os.path.join(EXP_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    b = results[best_stat]
    print(f"[EXP-0042] best={best_stat} rho_best={b['rho_best']} "
          f"rho_fixed98={b['rho_fixed98']} LOOwithin1={b['loo_within1']}")
    print(f"[EXP-0042] verdict={verdict} go_stats={go_stats} "
          f"({metrics['wall_s']}s wall; fresh detects {fresh_requested}/30)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
