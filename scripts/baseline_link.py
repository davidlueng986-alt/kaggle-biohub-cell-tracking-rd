#!/usr/bin/env python3
"""Oracle-detection causal linker baseline (CPU-only, no training).

Links GT node positions t->t+1 with per-pair optimal bipartite matching on
scaled um distance (7um gate), one-to-one, strictly causal (no future frames,
no cross-embryo state). Emits <=1 outgoing edge per node -> predicts zero
forks (division term expected 0; exercises PROTOCOL division sub-gate).

Usage:
  python3 scripts/baseline_link.py gt.json --out pred.json
"""
import json
import sys

VOXEL = (1.625, 0.40625, 0.40625)
MAXD = 7.0


def _hungarian(cost):
    # Pure-python O(n^3); exact behavior preserved for small N (oracle floor).
    # For dense inputs (N>60) link() prefers the scipy C path (same optimum).
    n = len(cost)
    if n == 0:
        return []
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            row = cost[i0 - 1]
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = row[j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    out = [-1] * n
    for j in range(1, n + 1):
        if p[j]:
            out[p[j] - 1] = j - 1
    return out


def _assign(cost):
    """Optimal assignment; scipy C path for N>60 (same optimum, deterministic),
    pure-python below (bit-exact legacy behavior for oracle graphs)."""
    n = len(cost)
    if n > 60:
        try:
            import numpy as np
            from scipy.optimize import linear_sum_assignment
            ri, ci = linear_sum_assignment(np.asarray(cost, dtype=float))
            out = [-1] * n
            for r, c in zip(ri.tolist(), ci.tolist()):
                out[r] = c
            _assign.backend = "scipy"
            return out
        except ImportError:
            pass
    _assign.backend = "pure"
    return _hungarian(cost)


_assign.backend = "pure"


def _pair(P, Q, maxd=MAXD):
    """Optimal gated assignment for one adjacent frame pair. Returns edges."""
    n, m = len(P), len(Q)
    if not n or not m:
        return []
    N = max(n, m)
    dummy = maxd + 1e-9
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
    A = _assign(C)
    return [[P[i]["id"], Q[j]["id"]] for i in range(n)
            if 0 <= (j := A[i]) < m and C[i][j] <= maxd]


def link(gt, maxd=MAXD):
    """maxd: linking gate um (method hyperparameter; scorer gate stays 7um
    per PROTOCOL v1.1. Default reproduces the frozen floor bit-exactly)."""
    by_t = {}
    for n in gt["nodes"]:
        by_t.setdefault(n["t"], []).append(n)
    ts = sorted(by_t)
    phased = any(n.get("split") for ns in by_t.values() for n in ns)
    edges = []
    for a, b in zip(ts, ts[1:]):
        if b != a + 1:
            continue  # only adjacent frames (causal chain links)
        P = sorted(by_t[a], key=lambda d: d["id"])
        Q = sorted(by_t[b], key=lambda d: d["id"])
        if not phased:
            edges.extend(_pair(P, Q, maxd))  # legacy single-Hungarian path
            continue
        # two-phase: primaries claim first (all targets visible, base intact),
        # split parts link only to leftovers (conservative, EXP-0013).
        prim = [n for n in P if not n.get("split")]
        frag = [n for n in P if n.get("split")]
        e1 = _pair(prim, Q, maxd)
        used = {v for _, v in e1}
        Qleft = [n for n in Q if n["id"] not in used]
        edges.extend(e1)
        edges.extend(_pair(frag, Qleft, maxd))
    edges.sort()
    return {"nodes": gt["nodes"], "edges": edges, "T_true": gt.get("T_true"),
            "voxel_size_um": list(VOXEL), "assign": _assign.backend,
            "phased": phased}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("gt", help="GT graph JSON from geff_to_graph.py")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    gt = json.load(open(a.gt))
    pred = link(gt)
    json.dump(pred, open(a.out, "w"))
    print(f"wrote {a.out} nodes={len(pred['nodes'])} "
          f"pred_edges={len(pred['edges'])} gt_edges={len(gt['edges'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
