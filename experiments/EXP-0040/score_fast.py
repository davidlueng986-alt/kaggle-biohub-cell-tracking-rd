#!/usr/bin/env python3
"""EXP-0040 scorer driver (lives inside EXP dir; scripts/* untouched on disk).

Same runtime-only solver swap as EXP-0039 (proven pattern): scripts/score.py
match_nodes uses a pure-Python O(N^3) Hungarian with N = max(n_pred, n_gt)
per frame. At @96.0 (~200+ det/frame) that is too slow for 200 frames.
At RUNTIME ONLY, replace score._hungarian with a scipy-backed exact solver
(scipy.optimize.linear_sum_assignment solves the identical min-cost bipartite
matching problem). scripts/score.py on disk is NOT modified.
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

SIDS = ["44b6_0b24845f", "44b6_0c582fdc"]
GT_DIR = os.path.join(ROOT, "experiments/EXP-0003/gt")
T_TRUE_EXPECT = {"44b6_0b24845f": 32795, "44b6_0c582fdc": 27958}


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
    """Prove scipy solver == pure-python solver on real frames."""
    for sid in SIDS:
        gt = json.load(open(os.path.join(GT_DIR, f"{sid}_gt.json")))
        gt_by_t = {}
        for n in gt["nodes"]:
            gt_by_t.setdefault(int(n["t"]), []).append(n)
        frames = [0, 20, 50, 99]
        for src, tag in (("EXP-0040", "pct96"), ("EXP-0021", "pct99")):
            for t in frames:
                p = os.path.join(ROOT, "experiments", src,
                                 f"full_{sid}_t{t}.json")
                if not os.path.exists(p):
                    continue
                det = json.load(open(p))
                P = sorted(det["nodes"], key=lambda d: d["id"])
                G = sorted(gt_by_t.get(t, []), key=lambda d: d["id"])
                n, m = len(P), len(G)
                N = max(n, m)
                if N == 0:
                    continue
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
                assert abs(c_ref - c_fast) < 1e-6, (sid, src, t, c_ref, c_fast)
                m_ref = {(P[i]["id"], G[a_ref[i]]["id"]) for i in range(n)
                         if 0 <= a_ref[i] < m and cost[i][a_ref[i]] <= 7.0}
                m_fast = {(P[i]["id"], G[a_fast[i]]["id"]) for i in range(n)
                          if 0 <= a_fast[i] < m and cost[i][a_fast[i]] <= 7.0}
                assert m_ref == m_fast, (sid, src, t, "pair mismatch")
                print(f"  equiv OK {sid} {tag} t={t}: n_pred={n} n_gt={m} "
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

    out = {"samples": {}, "scorer": {
        "protocol": None, "scorer_version": None,
        "solver": ("scipy linear_sum_assignment (runtime-only, "
                   "equivalence-gated vs pure-python Hungarian)"),
        "scripts_unmodified": True}}
    for sid in SIDS:
        gt = json.load(open(os.path.join(GT_DIR, f"{sid}_gt.json")))
        assert gt.get("T_true") == T_TRUE_EXPECT[sid], (sid, gt.get("T_true"))
        gt_by_t = {}
        for n in gt["nodes"]:
            gt_by_t.setdefault(int(n["t"]), []).append(n)

        # ---- @96.0 diagnostics (recall/det/timing) + trusted score
        det_total, times, recs = 0, [], []
        for t in range(100):
            det = json.load(open(os.path.join(EXP_DIR, f"full_{sid}_t{t}.json")))
            times.append(det["params"]["elapsed_s"])
            det_total += len(det["nodes"])
            g = gt_by_t.get(t, [])
            if g:
                recs.append(frame_recall(det["nodes"], g))
        recall96 = sum(recs) / len(recs) if recs else 0.0
        s_f = sum(times) / len(times)
        print(f"{sid} @96.0: det_total={det_total} det/f={det_total/100:.2f} "
              f"recall={recall96:.4f} s_f={s_f:.4f}", flush=True)

        pred96 = json.load(open(os.path.join(EXP_DIR, f"{sid}_pred.json")))
        ts = time.time()
        agg96 = SC.score_samples([(sid, pred96, gt, None)])
        print(f"  score96 took {time.time()-ts:.1f}s", flush=True)
        s96 = agg96["per_sample"][0]
        print(json.dumps(s96, indent=2), flush=True)

        # ---- @99.0 baseline RECOMPUTE: fresh scorer run on frozen EXP-0021 pred
        pred99 = json.load(open(os.path.join(
            ROOT, "experiments/EXP-0021", f"{sid}_pred.json")))
        ts = time.time()
        agg99 = SC.score_samples([(sid, pred99, gt, None)])
        print(f"  score99-rescore took {time.time()-ts:.1f}s", flush=True)
        s99 = agg99["per_sample"][0]
        print(json.dumps(s99, indent=2), flush=True)

        out["samples"][sid] = {
            "p96": {"recall": recall96, "det_f": det_total / 100,
                    "gid": det_total, "s_f": s_f,
                    "T_ratio": det_total / s99["T_true"],
                    "edge": s96["adjusted_edge_jaccard"],
                    "raw": s96["edge_jaccard_raw"],
                    "div": s96["division_jaccard"],
                    "score": s96["score"], "ec": s96["edge_counts"],
                    "dc": s96["division_counts"], "T_true": s96["T_true"],
                    "assign": pred96.get("assign")},
            "p99_rescored": {"edge": s99["adjusted_edge_jaccard"],
                             "raw": s99["edge_jaccard_raw"],
                             "div": s99["division_jaccard"],
                             "score": s99["score"],
                             "ec": s99["edge_counts"],
                             "dc": s99["division_counts"],
                             "T_true": s99["T_true"], "T_pred": s99["T_pred"],
                             "T_ratio": s99["T_pred"] / s99["T_true"]},
        }
        out["scorer"]["protocol"] = agg96["protocol_version"]
        out["scorer"]["scorer_version"] = agg96["scorer_version"]
    out["wall_s"] = time.time() - t0
    json.dump(out, open(os.path.join(EXP_DIR, "scores.json"), "w"), indent=2)
    print(f"WROTE scores.json wall={out['wall_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
