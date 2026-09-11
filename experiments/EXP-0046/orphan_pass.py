#!/usr/bin/env python3
"""EXP-0046 (experiment-local): orphan-driven second-edge pass.

Base = baseline_link gate-7 links on detected nodes (imported, not copied).
Global re-id across frames first (det/pred files may restart ids per frame):
  sort by (t, old id), assign gid 1..N deterministically.

Pass: for each base edge u->v, find unmatched-as-target nodes w at time t(v),
w != v, within 10um (scaled, voxel z=1.625/y=x=0.40625) of v, such that
w has NO incoming edge AND u has exactly 1 outgoing edge; add u->w
(nearest such w only, one extra per source).

Differs from EXP-0044 r10 ONLY in the incoming-less requirement on w
(orphan-driven, not radius-driven).

Usage:
  python3 orphan_pass.py <det_pred.json> --out-pass pass.json --out-base base.json [--report report.json]
Writes pass/base graphs (gid nodes) + report (added edges, fork counts).
Deterministic, CPU-only.
"""
import json
import sys

sys.path.insert(0, "/home/box/workspace/kaggle-biohub-rd/scripts")
import baseline_link as bl

VOXEL = (1.625, 0.40625, 0.40625)
R_UM = 10.0


def um_dist(a, b):
    dz = (a["z"] - b["z"]) * VOXEL[0]
    dy = (a["y"] - b["y"]) * VOXEL[1]
    dx = (a["x"] - b["x"]) * VOXEL[2]
    return (dz * dz + dy * dy + dx * dx) ** 0.5


def reid(nodes):
    """Global re-id: sort by (t, old id), assign gid 1..N."""
    srt = sorted(nodes, key=lambda n: (int(n["t"]), int(n["id"])))
    new, old2new = [], {}
    for i, n in enumerate(srt, start=1):
        old2new[(int(n["t"]), int(n["id"]))] = i
        new.append({"id": i, "t": int(n["t"]), "z": n["z"], "y": n["y"], "x": n["x"]})
    return new, old2new


def orphan_second_edge(base):
    nodes = base["nodes"]
    by_id = {n["id"]: n for n in nodes}
    by_t = {}
    for n in nodes:
        by_t.setdefault(int(n["t"]), []).append(n)
    out = {}
    inn = {}
    for u, v in base["edges"]:
        out.setdefault(u, []).append(v)
        inn.setdefault(v, []).append(u)
    added = []
    best_per_source = {}  # u -> (dist, v, w)
    for u, v in sorted(base["edges"]):
        if len(out.get(u, [])) != 1:
            continue
        bv = by_id[v]
        tv = int(bv["t"])
        best = None
        for w in sorted(by_t.get(tv, []), key=lambda n: n["id"]):
            wid = w["id"]
            if wid == v:
                continue
            if inn.get(wid):
                continue  # orphan (incoming-less) requirement
            d = um_dist(bv, w)
            if d <= R_UM and (best is None or d < best[0] or (d == best[0] and wid < best[1])):
                best = (d, wid)
        if best is not None:
            d, wid = best
            cur = best_per_source.get(u)
            if cur is None or d < cur[0] or (d == cur[0] and wid < cur[2]):
                best_per_source[u] = (d, v, wid)
    eset = set(map(tuple, base["edges"]))
    for u in sorted(best_per_source):
        d, v, w = best_per_source[u]
        if (u, w) not in eset:
            added.append([u, w])
            eset.add((u, w))
    added.sort()
    return added


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("det")
    ap.add_argument("--out-pass", required=True)
    ap.add_argument("--out-base", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    det = json.load(open(a.det))
    nodes, _ = reid(det["nodes"])
    det_g = {"nodes": nodes, "edges": [], "T_true": det.get("T_true")}
    base = bl.link(det_g, maxd=7.0)
    added = orphan_second_edge(base)
    edges = sorted(set(map(tuple, base["edges"])) | set(map(tuple, added)))
    outdeg = {}
    for u, v in edges:
        outdeg[u] = outdeg.get(u, 0) + 1
    forks = sum(1 for c in outdeg.values() if c >= 2)
    # base fork count: nodes with >=2 outgoing in base
    bout = {}
    for u, v in base["edges"]:
        bout[u] = bout.get(u, 0) + 1
    n_base_forks = sum(1 for c in bout.values() if c >= 2)
    psg = {"nodes": nodes, "edges": [list(e) for e in edges],
           "T_true": det.get("T_true"), "voxel_size_um": list(VOXEL)}
    bsg = {"nodes": nodes, "edges": [list(e) for e in base["edges"]],
           "T_true": det.get("T_true"), "voxel_size_um": list(VOXEL)}
    json.dump(bsg, open(a.out_base, "w"))
    json.dump(psg, open(a.out_pass, "w"))
    rep = {"n_nodes": len(nodes), "n_base_edges": len(base["edges"]),
           "n_added": len(added), "added": added,
           "n_pass_edges": len(edges), "n_base_forks": n_base_forks,
           "n_pass_forks": forks}
    if a.report:
        json.dump(rep, open(a.report, "w"), indent=2)
    print(json.dumps(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
