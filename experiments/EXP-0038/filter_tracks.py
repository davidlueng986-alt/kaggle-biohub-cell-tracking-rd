#!/usr/bin/env python3
"""EXP-0038: T-discipline track filter (post-processing ONLY on frozen graphs).

Steps (deterministic, sorted iteration, CPU-only):
  (a) Drop tracks (weakly-connected components over node/edge graph) whose
      frame length (# distinct t values in the component) is < MIN_LEN (6).
  (b) Prune isolated single nodes (degree 0). Note: these are length-1
      components, so they are already dropped by (a); this pass is explicit
      (and idempotent) for auditability.
  (c) Frac-capped rescue: greedily re-add dropped tracks, longest first
      (key: -frame_len, -node_count, min node id), whole tracks only, while
      total re-added nodes <= RESCUE_FRAC * (# kept nodes).

Cap choice (documented): RESCUE_FRAC = 0.05 (5% of kept nodes) mirrors the
same-account Lineage Forge reference (min-track-len 6 + prune-isolated +
frac-capped rescue). Rationale: count discipline under PROTOCOL v1.1 — the
T_true penalty factor 1 - a*(T_pred-T_true)/T_true (a=0.1) and the sparse-GT
FP rules punish unfiltered dense output, so the rescue budget must keep
T_pred nearly fixed while recovering only the longest near-threshold tracks.
A relative (fraction-of-kept) cap, rather than an absolute count, scales
across videos of very different density (here: 4723 vs 26168 dets).

Usage:
  python3 filter_tracks.py --in pred.json --out filtered.json [--min-len 6] [--rescue-frac 0.05]
"""

import argparse
import json
import sys


def load_graph(path):
    with open(path) as f:
        d = json.load(f)
    return d


def weakly_connected_components(node_ids, edges):
    """Union-find over node ids; edges with missing endpoints are ignored
    (counted as dangling). Returns (components, n_dangling)."""
    parent = {nid: nid for nid in node_ids}
    dangling = 0

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            # deterministic root: smaller id wins
            if ra > rb:
                ra, rb = rb, ra
            parent[rb] = ra

    for u, v in edges:
        if u in parent and v in parent:
            union(u, v)
        else:
            dangling += 1
    comp = {}
    for nid in sorted(node_ids):
        comp.setdefault(find(nid), []).append(nid)
    return comp, dangling


def filter_graph(pred, min_len=6, rescue_frac=0.05):
    nodes = pred.get("nodes", [])
    edges = [tuple(e) for e in pred.get("edges", [])]
    by_id = {n["id"]: n for n in nodes}

    comp, n_dangling = weakly_connected_components(sorted(by_id), edges)

    # degree (undirected, over valid edges only) for the isolated-node audit
    degree = {nid: 0 for nid in by_id}
    for u, v in edges:
        if u in degree and v in degree:
            degree[u] += 1
            degree[v] += 1

    kept = {}    # root -> member list
    dropped = {}  # root -> member list
    for root in sorted(comp):
        members = comp[root]
        frame_len = len({by_id[m]["t"] for m in members})
        if frame_len < min_len:
            dropped[root] = members
        else:
            kept[root] = members

    # (b) explicit isolated-node pass (audit: must already be in dropped)
    isolated = sorted([nid for nid, d in degree.items() if d == 0])
    isolated_not_dropped = [nid for nid in isolated
                            if not any(nid in m for m in dropped.values())
                            and not any(nid in m for m in kept.values())]
    # isolated nodes are single-member components; verify subsumption
    n_isolated = len(isolated)
    isolated_in_dropped = sum(1 for nid in isolated
                              if any(nid in m for m in dropped.values()))

    kept_nodes = sorted([nid for members in kept.values() for nid in members])
    kept_set = set(kept_nodes)

    # (c) frac-capped rescue: longest dropped tracks first, whole tracks only
    budget = int(rescue_frac * len(kept_set)) if kept_set else 0
    candidates = sorted(
        dropped.values(),
        key=lambda m: (-len({by_id[i]["t"] for i in m}), -len(m), min(m)),
    )
    rescued = []
    rescued_nodes = 0
    for members in candidates:
        if rescued_nodes + len(members) <= budget:
            rescued.append(members)
            rescued_nodes += len(members)
    rescued_set = {nid for members in rescued for nid in members}
    final_set = kept_set | rescued_set

    out_nodes = sorted((by_id[nid] for nid in final_set), key=lambda n: n["id"])
    out_edges = sorted(
        [[u, v] for u, v in edges if u in final_set and v in final_set]
    )

    out = dict(pred)  # pass through extra keys (voxel_size_um, assign, ...)
    out["nodes"] = out_nodes
    out["edges"] = out_edges
    stats = {
        "min_len": min_len,
        "rescue_frac": rescue_frac,
        "n_nodes_in": len(nodes),
        "n_edges_in": len(edges),
        "n_components": len(comp),
        "n_dangling_edges_ignored": n_dangling,
        "n_kept_components": len(kept),
        "n_dropped_components": len(dropped),
        "n_isolated_nodes": n_isolated,
        "n_isolated_in_dropped": isolated_in_dropped,
        "n_kept_nodes": len(kept_set),
        "n_rescued_tracks": len(rescued),
        "n_rescued_nodes": rescued_nodes,
        "rescue_budget_nodes": budget,
        "n_nodes_out": len(out_nodes),
        "n_edges_out": len(out_edges),
    }
    return out, stats


def main(argv=None):
    ap = argparse.ArgumentParser(description="EXP-0038 T-discipline filter")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--min-len", type=int, default=6)
    ap.add_argument("--rescue-frac", type=float, default=0.05)
    ap.add_argument("--stats-out", default=None)
    args = ap.parse_args(argv)
    pred = load_graph(args.inp)
    out, stats = filter_graph(pred, args.min_len, args.rescue_frac)
    with open(args.out, "w") as f:
        json.dump(out, f)
    print(json.dumps(stats, indent=2))
    if args.stats_out:
        with open(args.stats_out, "w") as f:
            json.dump(stats, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
