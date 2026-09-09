#!/usr/bin/env python3
"""Fork-proposing linker variant (EXP-0004, CPU-only, deterministic).

Builds on the EXP-0003 oracle causal Hungarian links, then proposes forks
from LOCAL crowding evidence only:
  for each source u with exactly 1 outgoing edge u->v, if another node w
  at the same timepoint as v, w != v, within 7um (scaled) of v, and w has
  no incoming edge yet, add u->w (nearest such w only, one extra per source).

Rationale: a dividing parent's two daughters appear close together but
separate fast (observed 8.5-12.5um on subset GT) — beyond the 7um matching
gate. The PROPOSAL radius is therefore a separate declared hyperparameter
(default 15um); the MATCHING gate stays 7um. This is the geometry-only
precursor to H-003 appearance gating.

Causality: uses only nodes at t and t+1 (same pair as the base link).
No cross-embryo state. Deterministic.

Usage:
  python3 scripts/fork_link.py gt.json --out pred.json
"""
import json

import baseline_link as BL

VOXEL = BL.VOXEL
MAXD = BL.MAXD
PROPOSE_UM = 15.0  # fork-proposal radius (declared hyperparameter, see header)


def _dist(a, b):
    dz = (a["z"] - b["z"]) * VOXEL[0]
    dy = (a["y"] - b["y"]) * VOXEL[1]
    dx = (a["x"] - b["x"]) * VOXEL[2]
    return (dz * dz + dy * dy + dx * dx) ** 0.5


def link(gt, propose_um=PROPOSE_UM):
    base = BL.link(gt)
    nodes = {n["id"]: n for n in gt["nodes"]}
    out = {}
    inn = {}
    for u, v in base["edges"]:
        out.setdefault(u, []).append(v)
        inn.setdefault(v, []).append(u)
    by_t = {}
    for n in gt["nodes"]:
        by_t.setdefault(n["t"], []).append(n)
    extra = 0
    edges = [list(e) for e in base["edges"]]
    for u in sorted(out):
        if len(out[u]) != 1:
            continue
        v = out[u][0]
        vt = nodes[v]["t"]
        best = None
        for w in by_t.get(vt, []):
            if w["id"] == v or w["id"] in inn:
                continue
            d = _dist(nodes[v], w)
            if d <= propose_um and (best is None or d < best[0]):
                best = (d, w["id"])
        if best is not None:
            edges.append([u, best[1]])
            out[u].append(best[1])
            inn.setdefault(best[1], []).append(u)
            extra += 1
    edges.sort()
    return {"nodes": gt["nodes"], "edges": edges, "T_true": gt.get("T_true"),
            "voxel_size_um": list(VOXEL), "n_fork_extra": extra}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("gt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--propose-um", type=float, default=PROPOSE_UM)
    a = ap.parse_args(argv)
    gt = json.load(open(a.gt))
    pred = link(gt, propose_um=a.propose_um)
    json.dump(pred, open(a.out, "w"))
    print(f"wrote {a.out} nodes={len(pred['nodes'])} "
          f"edges={len(pred['edges'])} fork_extra={pred['n_fork_extra']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
