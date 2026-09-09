#!/usr/bin/env python3
"""Trusted scorer v1.1 (faithful mirror) for BioHub cell-tracking.

Metric spec (normative):
  https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
Competition pages (voxel scale, submission format, T_true provenance):
  slug biohub-cell-tracking-during-development
  - voxel scale z=1.625, y=0.40625, x=0.40625 um/voxel (Data + Evaluation tabs)
  - T_true = `estimated_number_of_nodes` in .geff zarr.json metadata
  - submission.csv columns: id,dataset,row_type,node_id,t,z,y,x,source_id,target_id
  - node matching: per-timepoint optimal bipartite on scaled centroid dist, max 7.0 um
  - scores CAN exceed 1.0 (under-prediction inflates adjusted term)

score = adjusted_edge_jaccard + 0.1 * division_jaccard
  - edge TP/FP/FN with sparse-aware FP rule (two listed cases only)
  - adjusted = max(0, jaccard * (1 - a*(T_pred-T_true)/T_true)), a=0.1
  - division = local window grandparent->parent->children->grandchildren, +-1tp
  - aggregation: adjusted edge = per-sample adjusted weighted by w_i=TP+FP+FN;
    division = summed TP/FP/FN micro-average.

Input formats (auto-detected):
  JSON single-sample geff-like:
    {"nodes":[{"id":1,"t":0,"z":32,"y":128,"x":128},...],
     "edges":[[1,2],...], "T_true":123 (optional),
     "voxel_size_um":[1.625,0.40625,0.40625] (optional)}
  JSON legacy toy (backward compat, flagged simplified:true):
    {"edges":[[u,v],...], "divisions":[[p,d1,d2],...]}
  CSV (submission.csv format): --pred/--gt ending in .csv are grouped by
    `dataset` column into per-sample graphs and micro-averaged.

Usage:
  python3 scripts/score.py --dry-run
  python3 scripts/score.py --pred pred.json --gt gt.json [--out metrics.json]
  python3 scripts/score.py --pred pred.csv --gt gt.csv [--out metrics.json]
  python3 scripts/score.py --pred pred.json --gt gt.json --T-true 500

Deps: stdlib + numpy only. No scipy (Hungarian implemented below).
Deterministic: sorted iteration, no randomness.

PROTOCOL v1.1 delta vs v1.0 SIMPLIFIED:
  v1.0 score.py was plain set-Jaccard over ID tuples (no geometry, no sparse
  rule, no T_true penalty, no division window). v1.1 implements all five
  stages per metrics.md. Legacy toy inputs still score via the old path so
  EXP-0001 dry-run (fold0 0.5/1.0/0.6) keeps passing.
  Known approximation (documented): division local re-matching uses the global
  per-timepoint match restricted to the GT window instead of an independent
  per-window optimal assignment; cross-component evidence uses weakly
  connected GT components. Both are conservative (fewer TPs, never inflated).
"""

import argparse
import csv
import json
import sys

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

PROTOCOL_VERSION = "1.1"
SCORER_VERSION = "1.1.0"
DEFAULT_VOXEL = (1.625, 0.40625, 0.40625)
MAX_DIST_UM = 7.0
DIV_W = 0.1
ADJ_A = 0.1
BIG = 1e9


# ---------------------------------------------------------------- Hungarian
def _hungarian(cost):
    """Min-cost assignment for square cost matrix (list of lists / 2D array).

    Returns col_for_row list length n. Pure-python O(n^3) (Emaxx impl).
    Deterministic. n=0 -> [].
    """
    n = len(cost)
    if n == 0:
        return []
    # 1-indexed arrays
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
            ci0 = cost[i0 - 1]
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = ci0[j - 1] - u[i0] - v[j]
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
    col_for_row = [-1] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            col_for_row[p[j] - 1] = j - 1
    return col_for_row


def _um_dist(a, b, voxel):
    dz = (a[0] - b[0]) * voxel[0]
    dy = (a[1] - b[1]) * voxel[1]
    dx = (a[2] - b[2]) * voxel[2]
    return (dz * dz + dy * dy + dx * dx) ** 0.5


# ------------------------------------------------------------ node matching
def match_nodes(pred_nodes, gt_nodes, voxel=DEFAULT_VOXEL, max_dist=MAX_DIST_UM):
    """Per-timepoint optimal bipartite match on scaled centroid distance.

    pred_nodes/gt_nodes: list of dicts {id,t,z,y,x}. Returns
    (pred_to_gt dict, gt_to_pred dict). One-to-one, threshold inclusive.
    """
    pred_by_t = {}
    for n in pred_nodes:
        pred_by_t.setdefault(int(n["t"]), []).append(n)
    gt_by_t = {}
    for n in gt_nodes:
        gt_by_t.setdefault(int(n["t"]), []).append(n)
    pred_to_gt = {}
    gt_to_pred = {}
    for t in sorted(set(pred_by_t) | set(gt_by_t)):
        P = sorted(pred_by_t.get(t, []), key=lambda d: d["id"])
        G = sorted(gt_by_t.get(t, []), key=lambda d: d["id"])
        n, m = len(P), len(G)
        if n == 0 or m == 0:
            continue
        N = max(n, m)
        dummy = max_dist + 1e-9
        cost = [[0.0] * N for _ in range(N)]
        for i in range(N):
            for j in range(N):
                if i < n and j < m:
                    d = _um_dist(
                        (P[i]["z"], P[i]["y"], P[i]["x"]),
                        (G[j]["z"], G[j]["y"], G[j]["x"]),
                        voxel,
                    )
                    cost[i][j] = d if d <= max_dist else BIG
                elif i < n:  # real pred -> dummy gt (leave unmatched)
                    cost[i][j] = dummy
                else:  # dummy pred row
                    cost[i][j] = 0.0
        assign = _hungarian(cost)
        for i in range(n):
            j = assign[i]
            if 0 <= j < m and cost[i][j] <= max_dist:
                pred_to_gt[P[i]["id"]] = G[j]["id"]
                gt_to_pred[G[j]["id"]] = P[i]["id"]
    return pred_to_gt, gt_to_pred


# ------------------------------------------------------------- edge counts
def _adj(edges):
    out, inn = {}, {}
    for u, v in edges:
        out.setdefault(u, set()).add(v)
        inn.setdefault(v, set()).add(u)
    return out, inn


def edge_counts(pred_edges, gt_edges, pred_to_gt):
    """Sparse-aware edge TP/FP/FN per metrics.md.

    FP only when (target matched and GT target has any incoming) OR
    (source matched and GT source has any outgoing). Else ignored.
    Returns dict(TP,FP,FN).
    """
    gt_set = {(a, b) for a, b in gt_edges}
    gt_out, gt_in = _adj(gt_edges)
    # reverse index: which pred edge claims each gt edge
    claimed = set()
    TP = FP = 0
    for u, v in pred_edges:
        mu = pred_to_gt.get(u)
        mv = pred_to_gt.get(v)
        if mu is not None and mv is not None and (mu, mv) in gt_set:
            TP += 1
            claimed.add((mu, mv))
        else:
            case1 = mv is not None and len(gt_in.get(mv, ())) > 0
            case2 = mu is not None and len(gt_out.get(mu, ())) > 0
            if case1 or case2:
                FP += 1
            # else ignored (sparse regions)
    FN = len(gt_set - claimed)
    return {"TP": TP, "FP": FP, "FN": FN}


def edge_jaccard(counts):
    d = counts["TP"] + counts["FP"] + counts["FN"]
    return 1.0 if d == 0 else counts["TP"] / d


def adjust(jaccard, T_pred, T_true, a=ADJ_A):
    if T_true is None or T_true <= 0:
        return jaccard, False
    factor = 1.0 - a * (T_pred - T_true) / T_true
    return max(0.0, jaccard * factor), True


# ---------------------------------------------------------------- division
def _gt_components(gt_nodes_ids, gt_edges):
    parent = {i: i for i in gt_nodes_ids}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for u, v in gt_edges:
        if u in parent and v in parent:
            union(u, v)
    return {i: find(i) for i in gt_nodes_ids}


def _children_map(edges):
    m = {}
    for u, v in edges:
        m.setdefault(u, []).append(v)
    for k in m:
        m[k] = sorted(m[k])
    return m


def _parents_map(edges):
    m = {}
    for u, v in edges:
        m.setdefault(v, []).append(u)
    for k in m:
        m[k] = sorted(m[k])
    return m


def division_counts(pred_nodes, pred_edges, gt_nodes, gt_edges, pred_to_gt,
                    gt_to_pred):
    """Local-window division TP/FP/FN (faithful, conservative v1.1).

    GT divisions: gt nodes with >=2 outgoing. Pred forks: pred nodes with
    >=2 outgoing. Per-GT-window checks use global per-t match restricted to
    window + directed time ordering + sole-parent + same-component guards.
    Pairing via max-cardinality bipartite (augmenting path).
    """
    gt_by_id = {n["id"]: n for n in gt_nodes}
    pred_by_id = {n["id"]: n for n in pred_nodes}
    gt_ch = _children_map(gt_edges)
    gt_pa = _parents_map(gt_edges)
    pred_ch = _children_map(pred_edges)
    pred_pa = _parents_map(pred_edges)
    gt_ids = [n["id"] for n in gt_nodes]
    comp = _gt_components(gt_ids, gt_edges) if gt_ids else {}

    gt_divs = sorted([g for g, ch in gt_ch.items() if len(ch) >= 2])
    pred_forks = sorted([p for p, ch in pred_ch.items() if len(ch) >= 2])

    # Precompute GT window info per division
    gt_win = {}
    for g in gt_divs:
        children = sorted(gt_ch[g])
        # take first two children as daughter roots (spec: exactly two outgoing
        # for GT; if more, evaluate first two sorted — conservative note)
        droots = children[:2]
        grands = sorted(gt_pa.get(g, []))  # predecessors (grandparent side)
        lineage = {}  # daughter idx -> set of gt ids (child + grandchildren)
        for di, d in enumerate(droots):
            s = {d} | set(gt_ch.get(d, []))
            lineage[di] = s
        window = {g} | set(grands) | set().union(*lineage.values()) if lineage else {g}
        gt_win[g] = {"droots": droots, "grands": grands, "lineage": lineage,
                     "window": window}

    def fork_recovers(g, f):
        """Does pred fork f recover GT division g?"""
        W = gt_win[g]
        # --- parent anchor: some pred node matches g or its predecessor, and
        # f is that node or its immediate successor.
        anchor_pred = set()
        for gid in [g] + W["grands"]:
            pid = gt_to_pred.get(gid)
            if pid is not None:
                anchor_pred.add(pid)
                anchor_pred.update(pred_ch.get(pid, []))
        if f not in anchor_pred:
            return False
        # --- branch structure: pred branches of f
        branches = sorted(pred_ch.get(f, []))
        if len(branches) < 2:
            return False
        # branch subtree ids (child + grandchildren)
        br_sub = {b: ({b} | set(pred_ch.get(b, []))) for b in branches}
        # GT lineage match matrix: lineage di x branch b
        # match if any pred node in branch subtree matches any gt node in lineage
        # with directed time order (pred match t >= fork t? downstream)
        ft = pred_by_id[f]["t"] if f in pred_by_id else None
        mat = {}
        for di, lset in W["lineage"].items():
            for b, bset in br_sub.items():
                ok = False
                for pid in bset:
                    gid = pred_to_gt.get(pid)
                    if gid is not None and gid in lset:
                        # directed: daughter evidence downstream of fork
                        if ft is None or pred_by_id[pid]["t"] > ft or (
                                pid != f and pred_by_id[pid]["t"] >= ft):
                            ok = True
                            break
                mat[(di, b)] = ok
        # bipartite: 2 lineages -> distinct branches (2xB). brute force.
        found = False
        for i in range(len(branches)):
            for j in range(len(branches)):
                if i == j:
                    continue
                if mat.get((0, branches[i])) and mat.get((1, branches[j])):
                    found = True
                    # valid branch evidence + unmerged checks for this pair
                    pair = [(0, branches[i]), (1, branches[j])]
                    if _branches_valid(pair, W, f, br_sub, comp, pred_to_gt,
                                       pred_pa, pred_ch, gt_to_pred):
                        return True
        return False

    def _branches_valid(pair, W, f, br_sub, comp, pred_to_gt, pred_pa,
                        pred_ch, gt_to_pred):
        # unmerged: direct child sole parent == f; grandchild fallback sole parent
        for _, b in pair:
            parents = pred_pa.get(b, [])
            if not (len(parents) == 1 and parents[0] == f):
                # allow if b unmatched and grandchildren carry evidence?
                # spec: grandchild fallback each grandchild must belong to b alone
                # still require sole-parent for b itself (conservative)
                return False
            for gc in pred_ch.get(b, []):
                if gc in br_sub[b] and pred_to_gt.get(gc) is not None:
                    gpa = pred_pa.get(gc, [])
                    if not (len(gpa) == 1 and gpa[0] == b):
                        return False
        # same-component: matched evidence across the two branches must not
        # sit in different reliable GT components
        comps = set()
        for _, b in pair:
            for pid in br_sub[b]:
                gid = pred_to_gt.get(pid)
                if gid is not None and gid in comp:
                    # direct-child evidence precedence: prefer direct child
                    comps.add(comp[gid])
                    break
        if len(comps) > 1:
            return False
        return True

    # candidate matrix
    cand = {g: sorted([f for f in pred_forks if fork_recovers(g, f)])
            for g in gt_divs}
    # max-cardinality pairing (gt -> fork), augmenting path
    match_f = {}  # fork -> gt

    def bpm(g, seen):
        for f in cand.get(g, []):
            if f in seen:
                continue
            seen.add(f)
            if f not in match_f or bpm(match_f[f], seen):
                match_f[f] = g
                return True
        return False

    TP_pairs = {}
    for g in gt_divs:
        bpm(g, set())
    for f, g in match_f.items():
        TP_pairs[g] = f
    TP = len(TP_pairs)
    FN = len(gt_divs) - TP
    # FPs: non-TP forks with enough evidence to evaluate
    gt_nodes_with_out = {g for g in gt_ch}
    FP = 0
    for f in pred_forks:
        if f in match_f:
            continue
        evaluable = False
        # (a) fork matches annotated GT node with outgoing edges
        gid = pred_to_gt.get(f)
        if gid is not None and gid in gt_nodes_with_out:
            evaluable = True
        # (b) local candidate for some GT division (was in cand but unpaired/failed)
        if not evaluable and any(f in v for v in cand.values()):
            evaluable = True
        # (c) cross-component child evidence
        if not evaluable:
            bcomps = set()
            for b in pred_ch.get(f, []):
                for pid in [{b} | set(pred_ch.get(b, []))][0]:
                    gg = pred_to_gt.get(pid)
                    if gg is not None and gg in comp:
                        bcomps.add(comp[gg])
                        break
            if len(bcomps) > 1:
                evaluable = True
        # (d) merged local branches
        if not evaluable:
            for b in pred_ch.get(f, []):
                pa = pred_pa.get(b, [])
                if not (len(pa) == 1 and pa[0] == f):
                    evaluable = True
                    break
        if evaluable:
            FP += 1
        # else ignored (sparse, unannotated region)
    return {"TP": TP, "FP": FP, "FN": FN}


# ------------------------------------------------------------- legacy path
def _legacy_jaccard(pred_list, gt_list):
    p = {tuple(sorted(e)) for e in (pred_list or [])}
    g = {tuple(sorted(e)) for e in (gt_list or [])}
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    return len(p & g) / len(p | g)


def _is_legacy(d):
    return "nodes" not in d


def score_single(pred, gt, voxel=DEFAULT_VOXEL, max_dist=MAX_DIST_UM,
                 T_true_override=None):
    """Score one sample. Returns dict with counts + jaccards."""
    if _is_legacy(pred) and _is_legacy(gt):
        ej = _legacy_jaccard(pred.get("edges"), gt.get("edges"))
        dj = _legacy_jaccard(pred.get("divisions"), gt.get("divisions"))
        return {
            "adjusted_edge_jaccard": ej,
            "division_jaccard": dj,
            "score": ej + DIV_W * dj,
            "edge_counts": None,
            "division_counts": None,
            "simplified": True,
            "T_pred": None,
            "T_true": None,
        }
    pn = pred.get("nodes", [])
    gn = gt.get("nodes", [])
    pe = [tuple(e) for e in pred.get("edges", [])]
    ge = [tuple(e) for e in gt.get("edges", [])]
    vx = tuple(pred.get("voxel_size_um", gt.get("voxel_size_um", voxel)))
    vx = tuple(vx) if len(tuple(vx)) == 3 else DEFAULT_VOXEL
    p2g, g2p = match_nodes(pn, gn, voxel=vx, max_dist=max_dist)
    ec = edge_counts(pe, ge, p2g)
    ej = edge_jaccard(ec)
    T_pred = len(pn)
    T_true = T_true_override if T_true_override is not None else gt.get("T_true", pred.get("T_true"))
    adj, used_T = adjust(ej, T_pred, T_true)
    dc = division_counts(pn, pe, gn, ge, p2g, g2p)
    dd = edge_jaccard(dc)
    return {
        "adjusted_edge_jaccard": adj,
        "edge_jaccard_raw": ej,
        "division_jaccard": dd,
        "score": adj + DIV_W * dd,
        "edge_counts": ec,
        "division_counts": dc,
        "simplified": False,
        "T_pred": T_pred,
        "T_true": T_true,
        "T_true_used": used_T,
        "n_pred_matched": len(p2g),
        "n_gt_matched": len(g2p),
        "voxel_size_um": list(vx),
        "max_dist_um": max_dist,
    }


def score_samples(pairs, voxel=DEFAULT_VOXEL, max_dist=MAX_DIST_UM):
    """Micro-average over samples. pairs: list of (name, pred, gt, T_true_ov)."""
    per = []
    w_sum = 0.0
    adj_w = 0.0
    dTP = dFP = dFN = 0
    for name, pred, gt, Tov in pairs:
        s = score_single(pred, gt, voxel=voxel, max_dist=max_dist,
                         T_true_override=Tov)
        s["sample"] = name
        per.append(s)
        if s["simplified"]:
            # legacy: weight 1 each (no counts); still average
            adj_w += s["adjusted_edge_jaccard"]
            w_sum += 1.0
            # legacy divisions have no micro counts; approximate via jaccard only
        else:
            ec = s["edge_counts"]
            w = ec["TP"] + ec["FP"] + ec["FN"]
            if w == 0:
                w = 1  # avoid zero-weight skew; unpenalized sample
            adj_w += s["adjusted_edge_jaccard"] * w
            w_sum += w
            dc = s["division_counts"]
            dTP += dc["TP"]
            dFP += dc["FP"]
            dFN += dc["FN"]
    adj_edge = adj_w / w_sum if w_sum else 0.0
    dden = dTP + dFP + dFN
    # if all legacy, fall back to mean division jaccard
    if dden == 0 and per and all(p.get("simplified") for p in per):
        div_j = sum(p["division_jaccard"] for p in per) / len(per) if per else 0.0
    else:
        div_j = 1.0 if dden == 0 else dTP / dden
    return {
        "per_sample": per,
        "adjusted_edge_jaccard": adj_edge,
        "division_jaccard": div_j,
        "division_counts_sum": {"TP": dTP, "FP": dFP, "FN": dFN},
        "score": adj_edge + DIV_W * div_j,
        "protocol_version": PROTOCOL_VERSION,
        "scorer_version": SCORER_VERSION,
        "metric_spec": "https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md",
        "voxel_size_um": list(voxel),
        "max_dist_um": max_dist,
    }


# ------------------------------------------------------------------- I/O
def load_json(path):
    with open(path) as f:
        return json.load(f)


def graphs_from_csv(path):
    """Parse submission.csv into {dataset: graph} with voxel-int nodes."""
    ds = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["dataset"]
            g = ds.setdefault(d, {"nodes": [], "edges": []})
            if row["row_type"] == "node":
                g["nodes"].append({
                    "id": int(row["node_id"]),
                    "t": int(row["t"]),
                    "z": int(row["z"]),
                    "y": int(row["y"]),
                    "x": int(row["x"]),
                })
            elif row["row_type"] == "edge":
                g["edges"].append([int(row["source_id"]), int(row["target_id"])])
    for g in ds.values():
        g["nodes"].sort(key=lambda n: n["id"])
        g["edges"].sort()
    return ds


def load_graph(path):
    if path.endswith(".csv"):
        return ("csv", graphs_from_csv(path))
    return ("json", load_json(path))


def main(argv=None):
    ap = argparse.ArgumentParser(description="BioHub trusted scorer v1.1")
    ap.add_argument("--pred", help="Path to pred JSON/CSV")
    ap.add_argument("--gt", help="Path to gt JSON/CSV")
    ap.add_argument("--out", help="Optional path to write metrics JSON")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--T-true", type=int, default=None)
    ap.add_argument("--max-dist", type=float, default=MAX_DIST_UM)
    ap.add_argument("--voxel", default=",".join(map(str, DEFAULT_VOXEL)),
                    help="dz,dy,dx um/voxel")
    args = ap.parse_args(argv)
    voxel = tuple(map(float, args.voxel.split(",")))
    assert len(voxel) == 3, "--voxel must be dz,dy,dx"

    if args.dry_run:
        # backward-compat toy (legacy path) — must equal 0.5/1.0/0.6
        pred = {"edges": [[1, 2], [2, 3], [3, 4]], "divisions": [[1, 2, 3]]}
        gt = {"edges": [[1, 2], [2, 3], [4, 5]], "divisions": [[1, 2, 3]]}
        agg = score_samples([("dryrun", pred, gt, None)],
                            voxel=voxel, max_dist=args.max_dist)
        print(json.dumps(agg, indent=2))
        # geometric smoke: two nodes 1 voxel apart in y (~0.4um) must match
        gpred = {"nodes": [{"id": 1, "t": 0, "z": 32, "y": 128, "x": 128},
                           {"id": 2, "t": 1, "z": 32, "y": 128, "x": 128}],
                 "edges": [[1, 2]]}
        ggt = {"nodes": [{"id": 1, "t": 0, "z": 32, "y": 129, "x": 128},
                         {"id": 2, "t": 1, "z": 32, "y": 129, "x": 128}],
               "edges": [[1, 2]], "T_true": 2}
        g = score_samples([("geo", gpred, ggt, None)],
                          voxel=voxel, max_dist=args.max_dist)
        assert abs(g["per_sample"][0]["adjusted_edge_jaccard"] - 1.0) < 1e-9, \
            "geometric smoke failed (1-voxel y offset must match within 7um)"
        print("dry-run OK (v1.1 faithful scorer; legacy toy + geometric smoke pass)",
              flush=True)
        return 0

    if not args.pred or not args.gt:
        ap.error("provide --pred and --gt, or use --dry-run")
    pt, pv = load_graph(args.pred)
    gt_, gv = load_graph(args.gt)
    if pt == "csv" or gt_ == "csv":
        assert pt == "csv" and gt_ == "csv", "CSV scoring needs both sides CSV"
        names = sorted(set(pv) & set(gv))
        assert names, "no overlapping dataset names between pred/gt CSV"
        pairs = [(n, pv[n], gv[n], args.T_true) for n in names]
    else:
        pairs = [("sample0", pv, gv, args.T_true)]
    agg = score_samples(pairs, voxel=voxel, max_dist=args.max_dist)
    print(json.dumps(agg, indent=2))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(agg, f, indent=2)
        print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
