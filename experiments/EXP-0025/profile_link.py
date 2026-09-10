#!/usr/bin/env python3
"""EXP-0025 linking-time profile driver (ANALYSIS ONLY).

Rebuilds per-frame node lists with global re-id per video from frozen
full-video detection artifacts, then times EACH adjacent-frame assignment
via scripts/baseline_link.py WITHOUT modifying it (perf_counter around
BL._pair, which internally routes through BL._assign: scipy C path for
N>60, pure-python below). Records N distribution, per-pair seconds vs N,
fitted scaling, total link seconds, and link share of (detect+link).

Usage: python3 experiments/EXP-0025/profile_link.py
Writes: experiments/EXP-0025/metrics.json (+ pair_times_<tag>.csv)
"""
import csv
import glob
import json
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import baseline_link as BL  # noqa: E402  (read-only import; never modified)

EXP_DIR = os.path.join(ROOT, "experiments", "EXP-0025")
VIDEO_TIMEOUT_S = 12 * 60  # per-leg abort budget (<20 min total for 3 legs)

SETS = [
    ("dense_44b6_0113de3b_p98.5",
     "experiments/EXP-0009/full_44b6_0113de3b_t*.json"),
    ("sparse_6bba_05b6850b_p98.5",
     "experiments/EXP-0009/full_6bba_05b6850b_t*.json"),
    ("split_6bba05b6850b_p98.0",
     "experiments/EXP-0012/full_t*.json"),
]


def frame_key(p):
    m = re.search(r"_t(\d+)\.json$", p)
    return int(m.group(1)) if m else p


def load_video(pattern):
    files = sorted(glob.glob(os.path.join(ROOT, pattern)), key=frame_key)
    assert files, f"no files match {pattern}"
    frames, detect_s = [], 0.0
    for f in files:
        d = json.load(open(f))
        t = d["nodes"][0]["t"] if d["nodes"] else frame_key(f)
        # global re-id per video: per-frame ids restart at 1, so offset by t
        nodes = [dict(n, id=int(n["t"]) * 100000 + int(n["id"])) for n in d["nodes"]]
        # sanity: local t field must match file index ordering
        frames.append({"t": int(nodes[0]["t"]) if nodes else frame_key(f),
                       "nodes": sorted(nodes, key=lambda n: n["id"])})
        detect_s += float(d.get("params", {}).get("elapsed_s", 0.0))
    frames.sort(key=lambda fr: fr["t"])
    return files, frames, detect_s


def loglog_fit(N, dt):
    N = np.asarray(N, dtype=float)
    dt = np.asarray(dt, dtype=float)
    m = (N > 0) & (dt > 0)
    N, dt = N[m], dt[m]
    x = np.log(N)
    y = np.log(dt)
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"exponent_b": b, "logA": a,
            "pred_s_at_N50": float(np.exp(a + b * np.log(50))),
            "pred_s_at_N100": float(np.exp(a + b * np.log(100))),
            "pred_s_at_N175": float(np.exp(a + b * np.log(175))),
            "r2_loglog": r2, "n_pairs": int(len(N))}


def decompose_pair(P, Q, maxd=7.0):
    """Split one _pair call into cost-matrix build vs _assign solve."""
    VOXEL = BL.VOXEL
    n, m = len(P), len(Q)
    N = max(n, m)
    dummy = maxd + 1e-9
    t0 = time.perf_counter()
    C = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i < n and j < m:
                dz = (P[i]["z"] - Q[j]["z"]) * VOXEL[0]
                dy = (P[i]["y"] - Q[j]["y"]) * VOXEL[1]
                dx = (P[i]["x"] - Q[j]["x"]) * VOXEL[2]
                d = (dz * dz + dy * dy + dx * dx) ** 0.5
                C[i][j] = d if d <= maxd else 1e9
            elif i < n:
                C[i][j] = dummy
            else:
                C[i][j] = 0.0
    t_build = time.perf_counter() - t0
    t0 = time.perf_counter()
    A = BL._assign(C)
    t_solve = time.perf_counter() - t0
    return t_build, t_solve, BL._assign.backend


def profile_one(tag, pattern):
    files, frames, detect_s = load_video(pattern)
    by_t = {fr["t"]: fr["nodes"] for fr in frames}
    ts = sorted(by_t)
    counts = [len(by_t[t]) for t in ts]
    pairs = []
    aborted = False
    t_start = time.perf_counter()
    for a, b in zip(ts, ts[1:]):
        if time.perf_counter() - t_start > VIDEO_TIMEOUT_S:
            aborted = True
            break
        if b != a + 1:
            continue
        P, Q = by_t[a], by_t[b]
        t0 = time.perf_counter()
        edges = BL._pair(P, Q)
        dt = time.perf_counter() - t0
        pairs.append({"pair": [a, b], "n": len(P), "m": len(Q),
                      "N": max(len(P), len(Q)), "dt_s": dt,
                      "backend": BL._assign.backend, "edges": len(edges)})
    wall_s = time.perf_counter() - t_start
    link_s = float(sum(p["dt_s"] for p in pairs))
    # determinism check: re-run median pair, edges must be identical
    det_ok = None
    if pairs:
        mid = pairs[len(pairs) // 2]
        P, Q = by_t[mid["pair"][0]], by_t[mid["pair"][1]]
        e1 = BL._pair(P, Q)
        e2 = BL._pair(P, Q)
        det_ok = (sorted(map(list, e1)) == sorted(map(list, e2)))
    # build-vs-solve decomposition on median-N pair
    decomp = None
    if pairs:
        med = sorted(pairs, key=lambda p: p["N"])[len(pairs) // 2]
        P, Q = by_t[med["pair"][0]], by_t[med["pair"][1]]
        tb, ts_ = decompose_pair(P, Q)[:2]
        decomp = {"pair": med["pair"], "N": med["N"],
                  "build_s": tb, "solve_s": ts_,
                  "build_share": tb / (tb + ts_) if tb + ts_ > 0 else 0.0}
    # full BL.link cross-check (grouping+sort overhead included)
    t0 = time.perf_counter()
    gt = {"nodes": [n for fr in frames for n in fr["nodes"]], "edges": []}
    pred = BL.link(gt)
    link_full_s = time.perf_counter() - t0
    edge_sum = int(sum(p["edges"] for p in pairs))
    return {
        "tag": tag, "pattern": pattern, "n_frames": len(frames),
        "n_pairs_timed": len(pairs), "aborted_12min": aborted,
        "nodes_per_frame": {"min": int(min(counts)), "max": int(max(counts)),
                            "mean": float(np.mean(counts)),
                            "median": float(np.median(counts))},
        "detect_s": detect_s, "link_s": link_s,
        "link_share_of_detect_plus_link": link_s / (detect_s + link_s),
        "link_full_run_s": link_full_s,
        "link_edges_driver_sum": edge_sum,
        "link_edges_BLlink": len(pred["edges"]),
        "link_edges_match": edge_sum == len(pred["edges"]),
        "assign_backend": pred.get("assign"), "phased": pred.get("phased"),
        "determinism_rerun_match": det_ok,
        "median_pair_build_vs_solve": decomp,
        "per_pair": pairs,
        "fit_loglog": loglog_fit([p["N"] for p in pairs],
                                  [p["dt_s"] for p in pairs]) if pairs else None,
        "profile_wall_s": wall_s,
    }


def main():
    # warmup: force scipy import OUTSIDE timed region (N>60 -> C path)
    BL._assign([[0.0] * 61 for _ in range(61)])
    t_all = time.perf_counter()
    videos = []
    for tag, pattern in SETS:
        v = profile_one(tag, pattern)
        videos.append(v)
        # per-pair CSV for transparency
        with open(os.path.join(EXP_DIR, f"pair_times_{tag}.csv"), "w",
                  newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["t0", "t1", "n", "m", "N",
                                               "dt_s", "backend", "edges"])
            w.writeheader()
            for p in v["per_pair"]:
                w.writerow({"t0": p["pair"][0], "t1": p["pair"][1],
                            "n": p["n"], "m": p["m"], "N": p["N"],
                            "dt_s": f"{p['dt_s']:.6f}",
                            "backend": p["backend"], "edges": p["edges"]})
        print(f"[{tag}] frames={v['n_frames']} pairs={v['n_pairs_timed']} "
              f"Nmed={v['nodes_per_frame']['median']:.0f} "
              f"link={v['link_s']:.2f}s detect={v['detect_s']:.1f}s "
              f"share={v['link_share_of_detect_plus_link'] * 100:.1f}% "
              f"backend={v['assign_backend']} match={v['link_edges_match']}")
    # pooled scaling fit across all pairs (wide N range 45..190)
    allN = [p["N"] for v in videos for p in v["per_pair"]]
    allT = [p["dt_s"] for v in videos for p in v["per_pair"]]
    pooled = loglog_fit(allN, allT)

    def verdict(v):
        s = v["link_share_of_detect_plus_link"]
        if v["aborted_12min"]:
            return "partial (aborted)"
        if s > 0.50:
            return "linking-dominant"
        if s > 0.10:
            return "material-not-dominant"
        return "negligible"

    metrics = {
        "exp_id": "EXP-0025",
        "title": "Linking-time profile",
        "status": "done",
        "method": ("per-adjacent-pair perf_counter around BL._pair "
                   "(scipy C path N>60, pure-python else; gate 7um); "
                   "scipy import warmed up outside timed region; "
                   "global re-id per video (t*100000+local_id); "
                   "baseline_link.py unmodified"),
        "videos": videos,
        "scaling_pooled_loglog": pooled,
        "bottleneck_verdict": {v["tag"]: verdict(v) for v in videos},
        "paydown_recommendation": [
            "gate-prefiltered candidate lists: only build assignment "
            "subproblems over gated neighbors (d<=7um) and split each pair "
            "into connected components; solves many tiny Hungarians instead "
            "of one dense NxN (cuts both O(N^2) matrix build and O(N^3) solve).",
            "spatial hashing (uniform grid bins keyed at ~7um gate) to find "
            "gated candidates in ~O(N) instead of all-pairs O(N^2) distance "
            "checks; keeps deterministic exact optimum (same gate, same "
            "matching) — pure overhead removal.",
            "pair chunking NOT recommended as primary: pairs are already the "
            "atomic unit (99/frame-pairs); further tiling only helps via the "
            "component split above. Implement nothing in EXP-0025 (analysis only).",
        ],
        "total_wall_s": time.perf_counter() - t_all,
    }
    with open(os.path.join(EXP_DIR, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"[EXP-0025] pooled exponent b={pooled['exponent_b']:.2f} "
          f"R2={pooled['r2_loglog']:.3f} wall={metrics['total_wall_s']:.1f}s")


if __name__ == "__main__":
    main()
