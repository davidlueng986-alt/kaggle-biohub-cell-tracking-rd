#!/usr/bin/env python3
"""EXP-0057 scorer driver (lives inside EXP dir; scripts/* untouched on disk).

Same trusted-scorer performance situation as EXP-0039/EXP-0055:
scripts/score.py match_nodes uses a pure-Python O(N^3) Hungarian with
N = max(n_pred, n_gt) per frame. At @94.5 (denser than @95.5's ~433
det/frame) that is far too slow for 100 frames on CPU.

Solution: at RUNTIME ONLY, replace score._hungarian with a scipy-backed exact
solver (scipy.optimize.linear_sum_assignment solves the identical min-cost
bipartite matching problem). scripts/score.py on disk is NOT modified.
Equivalence gate below proves identical assignments on real frames before use.
All downstream logic (edge_counts/division_counts/adjust) runs unmodified.
"""
import json
import os
import sys
import time

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import score as SC  # noqa: E402  (trusted scorer v1.1.0, unmodified on disk)
from scipy.optimize import linear_sum_assignment  # noqa: E402
import numpy as np  # noqa: E402

SID = "6bba_05db0fb1"
PCT = "94.5"


def scipy_hungarian(cost):
    """Drop-in for score._hungarian: exact min-cost assignment, square matrix."""
    n = len(cost)
    if n == 0:
        return []
    c = np.asarray(cost, dtype=float)
    ri, ci = linear_sum_assignment(c)
    out = [-1] * n
    for r, cc in zip(ri.tolist(), ci.tolist()):
        out[r] = cc
    return out


def equivalence_gate():
    """Prove scipy solver == pure-python solver on real @94.5 frames."""
    gt = json.load(open(os.path.join(ROOT, "experiments/EXP-0003/gt",
                                     f"{SID}_gt.json")))
    gt_by_t = {}
    for n in gt["nodes"]:
        gt_by_t.setdefault(int(n["t"]), []).append(n)
    frames = [0, 20, 50, 99]
    for t in frames:
        p = os.path.join(EXP_DIR, f"full_{SID}_t{t}.json")
        det = json.load(open(p))
        P = sorted(det["nodes"], key=lambda d: d["id"])
        G = sorted(gt_by_t.get(t, []), key=lambda d: d["id"])
        n, m = len(P), len(G)
        N = max(n, m)
        dummy = 7.0 + 1e-9
        cost = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(N):
                if i < n and j < m:
                    dz = (P[i]["z"] - G[j]["z"]) * 1.625
                    dy = (P[i]["y"] - G[j]["y"]) * 0.40625
                    dx = (P[i]["x"] - G[j]["x"]) * 0.40625
                    dd = (dz * dz + dy * dy + dx * dx) ** 0.5
                    cost[i][j] = dd if dd <= 7.0 else 1e9
                elif i < n:
                    cost[i][j] = dummy
                else:
                    cost[i][j] = 0.0
        a_ref = SC._hungarian([row[:] for row in cost])
        a_fast = scipy_hungarian(cost)
        c_ref = sum(cost[i][a_ref[i]] for i in range(N))
        c_fast = sum(cost[i][a_fast[i]] for i in range(N))
        assert abs(c_ref - c_fast) < 1e-6, (t, c_ref, c_fast)
        m_ref = {(P[i]["id"], G[a_ref[i]]["id"]) for i in range(n)
                 if 0 <= a_ref[i] < m and cost[i][a_ref[i]] <= 7.0}
        m_fast = {(P[i]["id"], G[a_fast[i]]["id"]) for i in range(n)
                  if 0 <= a_fast[i] < m and cost[i][a_fast[i]] <= 7.0}
        assert m_ref == m_fast, (t, "pair mismatch")
        print(f"  equiv OK pct{PCT} t={t}: n_pred={n} n_gt={m} "
              f"cost={c_ref:.4f} pairs={len(m_ref)}", flush=True)
    print("EQUIVALENCE GATE PASSED", flush=True)


def frame_recall(det_nodes, gt_nodes_t):
    """Own diagnostic recall via scipy (not part of trusted scorer)."""
    from scipy.optimize import linear_sum_assignment as lsa
    n, m = len(det_nodes), len(gt_nodes_t)
    if n == 0 or m == 0:
        return 0.0
    C = np.zeros((n, m))
    for i, p in enumerate(det_nodes):
        for j, g in enumerate(gt_nodes_t):
            dz = (p["z"] - g["z"]) * 1.625
            dy = (p["y"] - g["y"]) * 0.40625
            dx = (p["x"] - g["x"]) * 0.40625
            C[i, j] = (dz * dz + dy * dy + dx * dx) ** 0.5
    ri, ci = lsa(C)
    return float(sum(1 for r, c in zip(ri, ci) if C[r, c] <= 7.0)) / m


def main():
    t0 = time.time()
    equivalence_gate()
    SC._hungarian = scipy_hungarian  # runtime-only solver swap (see docstring)

    gt = json.load(open(os.path.join(ROOT, "experiments/EXP-0003/gt",
                                     f"{SID}_gt.json")))
    assert gt.get("T_true") == 69800, gt.get("T_true")
    gt_by_t = {}
    for n in gt["nodes"]:
        gt_by_t.setdefault(int(n["t"]), []).append(n)

    # ---- @94.5 diagnostics (recall/det/timing) + trusted score
    det_total, times, recs = 0, [], []
    for t in range(100):
        det = json.load(open(os.path.join(EXP_DIR, f"full_{SID}_t{t}.json")))
        times.append(det["params"]["elapsed_s"])
        det_total += len(det["nodes"])
        g = gt_by_t.get(t, [])
        if g:
            recs.append(frame_recall(det["nodes"], g))
    recall = sum(recs) / len(recs)
    s_f = sum(times) / len(times)
    print(f"@94.5: det_total={det_total} det/f={det_total/100:.2f} "
          f"recall={recall:.4f} s_f={s_f:.4f}", flush=True)

    pred = json.load(open(os.path.join(EXP_DIR, f"{SID}_pred.json")))
    ts = time.time()
    agg = SC.score_samples([(SID, pred, gt, None)])
    print(f"score took {time.time()-ts:.1f}s", flush=True)
    s = agg["per_sample"][0]
    print(json.dumps(s, indent=2), flush=True)

    out = {
        "p945": {"recall": recall, "det_f": det_total / 100,
                 "gid": det_total, "s_f": s_f,
                 "T_ratio": det_total / s["T_true"],
                 "edge": s["adjusted_edge_jaccard"],
                 "raw": s["edge_jaccard_raw"],
                 "div": s["division_jaccard"],
                 "score": s["score"], "ec": s["edge_counts"],
                 "dc": s["division_counts"], "T_true": s["T_true"],
                 "T_pred": s["T_pred"],
                 "assign": pred.get("assign")},
        "scorer": {"protocol": agg["protocol_version"],
                   "scorer_version": agg["scorer_version"],
                   "solver": "scipy linear_sum_assignment (runtime-only, "
                             "equivalence-gated vs pure-python Hungarian)",
                   "scripts_unmodified": True},
        "wall_s": time.time() - t0,
    }
    json.dump(out, open(os.path.join(EXP_DIR, "scores.json"), "w"), indent=2)
    print(f"WROTE scores.json wall={out['wall_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
