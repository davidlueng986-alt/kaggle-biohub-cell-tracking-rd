#!/usr/bin/env python3
"""t->t+2 gap-closing pass (EXP-0017, CPU-only, deterministic).

Links unmatched sources at t to unmatched targets at t+2 within a widened
gate (default 14um ~ 2 frames of motion), one-to-one Hungarian, strictly
causal. Conservative default: sources that already have an outgoing edge
are skipped (never creates forks -> division-neutral by design);
--allow-forks lifts that guard (division sub-gate then applies).

Usage:
  python3 scripts/gap_link.py pred.json --out closed.json [--gap-um 14] [--allow-forks]
Input pred.json: {"nodes":[...], "edges":[[u,v]...]} (ids unique across t).
"""
import json
import sys

VOXEL = (1.625, 0.40625, 0.40625)


def gap_close(nodes, edges, gap_um=14.0, allow_forks=False):
    import baseline_link as BL
    by_t = {}
    for n in nodes:
        by_t.setdefault(n["t"], []).append(n)
    out = {u for u, _ in map(tuple, edges)}
    inn = {v for _, v in map(tuple, edges)}
    new_edges = [list(e) for e in edges]
    ts = sorted(by_t)
    for a, b in zip(ts, ts[1:]):
        if b != a + 2:
            continue
        P = sorted([n for n in by_t[a]
                    if allow_forks or n["id"] not in out], key=lambda d: d["id"])
        Q = sorted([n for n in by_t[b] if n["id"] not in inn], key=lambda d: d["id"])
        n, m = len(P), len(Q)
        if not n or not m:
            continue
        N = max(n, m)
        dummy = gap_um + 1e-9
        C = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(N):
                if i < n and j < m:
                    dz = (P[i]["z"] - Q[j]["z"]) * VOXEL[0]
                    dy = (P[i]["y"] - Q[j]["y"]) * VOXEL[1]
                    dx = (P[i]["x"] - Q[j]["x"]) * VOXEL[2]
                    dd = (dz * dz + dy * dy + dx * dx) ** 0.5
                    C[i][j] = dd if dd <= gap_um else 1e9
                elif i < n:
                    C[i][j] = dummy
                else:
                    C[i][j] = 0.0
        A = BL._assign(C)
        for i in range(n):
            j = A[i]
            if 0 <= j < m and C[i][j] <= gap_um:
                new_edges.append([P[i]["id"], Q[j]["id"]])
                out.add(P[i]["id"])
                inn.add(Q[j]["id"])
    new_edges.sort()
    return {"nodes": nodes, "edges": new_edges}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pred")
    ap.add_argument("--out", required=True)
    ap.add_argument("--gap-um", type=float, default=14.0)
    ap.add_argument("--allow-forks", action="store_true")
    a = ap.parse_args(argv)
    g = json.load(open(a.pred))
    out = gap_close(g["nodes"], g["edges"], a.gap_um, a.allow_forks)
    out["T_true"] = g.get("T_true")
    out["voxel_size_um"] = g.get("voxel_size_um", list(VOXEL))
    json.dump(out, open(a.out, "w"))
    print(f"wrote {a.out}: +{len(out['edges']) - len(g['edges'])} gap edges "
          f"({len(out['edges'])} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
