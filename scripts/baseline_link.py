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


def link(gt):
    by_t = {}
    for n in gt["nodes"]:
        by_t.setdefault(n["t"], []).append(n)
    ts = sorted(by_t)
    edges = []
    for a, b in zip(ts, ts[1:]):
        if b != a + 1:
            continue  # only adjacent frames (causal chain links)
        P = sorted(by_t[a], key=lambda d: d["id"])
        Q = sorted(by_t[b], key=lambda d: d["id"])
        n, m = len(P), len(Q)
        if not n or not m:
            continue
        N = max(n, m)
        dummy = MAXD + 1e-9
        C = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(N):
                if i < n and j < m:
                    dz = (P[i]["z"] - Q[j]["z"]) * VOXEL[0]
                    dy = (P[i]["y"] - Q[j]["y"]) * VOXEL[1]
                    dx = (P[i]["x"] - Q[j]["x"]) * VOXEL[2]
                    d = (dz * dz + dy * dy + dx * dx) ** 0.5
                    C[i][j] = d if d <= MAXD else 1e9
                elif i < n:
                    C[i][j] = dummy
                else:
                    C[i][j] = 0.0
        A = _hungarian(C)
        for i in range(n):
            j = A[i]
            if 0 <= j < m and C[i][j] <= MAXD:
                edges.append([P[i]["id"], Q[j]["id"]])
    edges.sort()
    return {"nodes": gt["nodes"], "edges": edges, "T_true": gt.get("T_true"),
            "voxel_size_um": list(VOXEL)}


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
