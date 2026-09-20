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
  AUDIT-FIX A2 REMOVES the first approximation: division_counts now rematches
  full-pred vs each GT window independently (official match_divisions parity,
  S11) with GT ==2 / fork-poison / considered-FP rules (S4-S7). The weakly
  connected component note still holds (official _gt_weak_component_ids).
"""
import argparse
import csv
import json
import math
import sys
import warnings

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    from scipy.spatial.distance import cdist as _cdist
    from scipy.sparse import csr_array as _csr_array
    from scipy.optimize import linear_sum_assignment as _lsap
    from scipy.sparse.csgraph import (
        min_weight_full_bipartite_matching as _mwfbm,
    )
    _HAVE_SCIPY = True
except ImportError:  # pragma: no cover
    _HAVE_SCIPY = False

PROTOCOL_VERSION = "1.1"
SCORER_VERSION = "1.2.0"
# AUDIT-FIX A1 (S1/S2/S3): match/filter/dedup mirror the official oracle:
#   tracking_cellmot 0.1.0 @ 075fc5f5a52d11077f9dc2b074644618f26939e2
#   (https://github.com/royerlab/kaggle-cell-tracking-competition, main 2026-07-17)
#   - S1 match_nodes: max-cardinality -> max-sum 1/(1+d) per timepoint, threshold
#     inclusive (tracksdata DistanceMatching.compute_weights + scipy
#     min_weight_full_bipartite_matching(maximize=True) with -1 fallback).
#   - S2: drop pred edges with t_target - t_source != 1 before counting
#     (metrics._evaluate_matched_graph consecutive-frame filter).
#   - S3: exact-duplicate dedup (keep lowest edge id) + merge-collapse onto the
#     same GT edge (keep lowest edge id) + out-degree>2 cap (keep 2 lowest
#     edge ids). Edge id = index in the pred edge list (insertion order).
# AUDIT-FIX A3 (S8/S9/S10/S13): aggregate mirrors the official oracle
#   (same pin; metrics.per_sample_metrics + metrics.summarise +
#   metrics.evaluate_datasets + scripts/evaluate.py):
#   - S8 T_true is GT-only (evaluate._read_estimated_n_total reads the GT
#     geff extra `estimated_number_of_nodes`, NaN if absent). A pred-supplied
#     T_true is NEVER used: GT missing T_true -> adj NaN -> sample excluded
#     from the adjusted average (official per_sample_metrics NaN rule).
#   - S9 zero-division run: official drops the term (division_jaccard NaN,
#     score = adjusted edge only, with a "No divisions" warning) — never
#     div_j = 1.0 (which white-sends +0.1).
#   - S10 edge_jaccard(0/0) is NaN (official _jaccard); zero-count samples
#     carry weight 0 and NaN adj, so summarise skips them (never weight 1);
#     T_true-missing samples are skipped the same way.
#   - S13 duplicate node ids: official csv_to_geffs keeps every row as a
#     distinct graph node and resolves edge refs to a duplicated node_id via
#     last-occurrence-wins (dict(zip(...))). score_single namespaces dup ids
#     the same way before match/edge/division stages so the match maps stay
#     one-to-one (no silent match loss, no one-to-many gt_to_pred).
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
def _match_group_scipy(Pc, Gc, voxel, max_dist):
    """tracksdata-exact per-timepoint assignment (S1).

    Replicates tracksdata.metrics.DistanceMatching.compute_weights +
    _match_single_frame bit-for-bit: float64 scale multiply, cdist,
    d <= max_dist (inclusive) mask in np.where (comp-major) order,
    weight     1/(1+d), float32 CSR with inferred shape, scipy
    min_weight_full_bipartite_matching(maximize=True), and on ValueError
    the -1 fill_empty retry, then the dense linear_sum_assignment fallback,
    both with isclose(-1) stripping. Implicit-zero pairs that complete the
    cover are KEPT as matches (official phantom-match quirk, S1).
    Pc/Gc: lists of raw (z,y,x). Returns list of (pred_pos, gt_pos).
    Requires scipy+numpy.
    """
    import numpy as _np
    scale_arr = _np.asarray(voxel, dtype=_np.float64)
    M = _np.asarray(Pc, dtype=_np.float64) * scale_arr
    N = _np.asarray(Gc, dtype=_np.float64) * scale_arr
    D = _cdist(M, N)
    comp_idx, ref_idx = _np.where(D <= max_dist)
    if len(ref_idx) == 0:
        return []
    rows = ref_idx.tolist()
    cols = comp_idx.tolist()
    dists = D[comp_idx, ref_idx]
    ious = (1.0 / (1.0 + dists)).tolist()
    weights = _csr_array((ious, (rows, cols)), dtype=_np.float32)
    try:
        rows_id, cols_id = _mwfbm(weights, maximize=True)
        values = weights[rows_id, cols_id]
        keep = _np.ones(len(rows_id), dtype=bool)
    except ValueError:
        # workaround: fill empty rows/cols with -1 and retry, then strip
        # matches on filled values (tracksdata _matching._match_single_frame)
        W = weights.copy()
        empty_rows = (W.sum(axis=1) == 0)
        empty_cols = (W.sum(axis=0) == 0)
        W[empty_rows, :] = -1.0
        W[:, empty_cols] = -1.0
        try:
            rows_id, cols_id = _mwfbm(W, maximize=True)
            values = W[rows_id, cols_id]
            keep = ~_np.isclose(values, -1.0)
        except ValueError:
            # dense fallback over -1-filled weights; implicit zeros (0.0)
            # survive the -1 strip and are kept as matches
            try:
                coo = W.tocoo()
                dense = _np.full(W.shape, -1.0, dtype=_np.float32)
                dense[coo.row, coo.col] = coo.data
                rows_id, cols_id = _lsap(dense, maximize=True)
                values = W[rows_id, cols_id]
                keep = ~_np.isclose(values, -1.0)
            except ValueError:  # official would crash here; stay robust
                return _match_group_hungarian(Pc, Gc, voxel, max_dist)
    return [(int(c), int(r)) for r, c, k in
            zip(rows_id.tolist(), cols_id.tolist(), keep.tolist()) if k]


def _match_group_hungarian(Pc, Gc, voxel, max_dist):
    """Pure-python fallback: max-cardinality -> max-sum 1/(1+d) (S1).

    Lexicographic (cardinality, weight) via min-cost Hungarian with a
    cardinality booster C = N+1 per allowed pair. Used when scipy is
    unavailable. Differs from the official only on zero-weight phantom
    pairs (official records sub-threshold pairs when they complete the
    smaller-side cover; the fallback leaves them unmatched).
    Pc/Gc: lists of raw (z,y,x). Returns list of (pred_pos, gt_pos).
    """
    n, m = len(Pc), len(Gc)
    N = max(n, m)
    C = float(N + 1)
    allow = [[False] * m for _ in range(n)]
    wmat = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            d = _um_dist(Pc[i], Gc[j], voxel)
            if d <= max_dist:
                allow[i][j] = True
                wmat[i][j] = 1.0 / (1.0 + d)
    cost = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i < n and j < m:
                cost[i][j] = -(C + wmat[i][j]) if allow[i][j] else BIG
            else:
                cost[i][j] = 0.0
    assign = _hungarian(cost)
    return [(i, j) for i in range(n)
            for j in [assign[i]] if 0 <= j < m and allow[i][j]]


def match_nodes(pred_nodes, gt_nodes, voxel=DEFAULT_VOXEL, max_dist=MAX_DIST_UM):
    """Per-timepoint optimal bipartite match on scaled centroid distance.

    Official rule (S1, tracking_cellmot 0.1.0 via tracksdata): per
    timepoint, max-weight matching covering the smaller side, with
    w = 1/(1+d) for d <= max_dist (inclusive) and 0 for disallowed pairs.
    With scipy available this runs the official procedure bit-for-bit
    (float32 CSR, min_weight_full_bipartite_matching(maximize=True), -1
    fallback + strip); zero-weight phantom pairs that complete the cover
    are recorded as matches exactly as the official does. Without scipy,
    a pure-python Hungarian fallback gives lexicographic
    (cardinality, weight) over allowed pairs only (phantoms unmatched).

    pred_nodes/gt_nodes: list of dicts {id,t,z,y,x}. Returns
    (pred_to_gt dict, gt_to_pred dict). Deterministic.
    """
    pred_by_t = {}
    for n in pred_nodes:
        pred_by_t.setdefault(int(n["t"]), []).append(n)
    gt_by_t = {}
    for n in gt_nodes:
        gt_by_t.setdefault(int(n["t"]), []).append(n)
    pred_to_gt = {}
    gt_to_pred = {}
    use_scipy = _HAVE_SCIPY and np is not None
    for t in sorted(set(pred_by_t) | set(gt_by_t)):
        P = sorted(pred_by_t.get(t, []), key=lambda d: d["id"])
        G = sorted(gt_by_t.get(t, []), key=lambda d: d["id"])
        if not P or not G:
            continue
        Pc = [(n["z"], n["y"], n["x"]) for n in P]
        Gc = [(n["z"], n["y"], n["x"]) for n in G]
        if use_scipy:
            pairs = _match_group_scipy(Pc, Gc, voxel, max_dist)
        else:
            pairs = _match_group_hungarian(Pc, Gc, voxel, max_dist)
        for i, j in pairs:
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


def _filter_pred_edges(pred_edges, pred_to_gt, t_of):
    """Official-order pred-edge preprocessing (S2/S3).

    Mirrors tracking_cellmot.metrics._evaluate_matched_graph:
      1. exact-duplicate dedup on (source, target), keep lowest edge id (S3);
      2. consecutive-frame filter, keep only t_target - t_source == 1 (S2);
         endpoints with unknown time are dropped (official left-join NULL
         rows fail the ==1 filter);
      3. merge-collapse: both-endpoints-matched edges mapping onto the same
         (matched_source, matched_target) pair keep the lowest edge id (S3);
      4. out-degree cap: per pred source keep the 2 lowest edge ids (S3).

    Edge id = index in pred_edges (insertion order, as in tracksdata).
    t_of: dict pred id -> t. Returns list of (idx, u, v) survivors.
    """
    # 1. exact-duplicate dedup, keep first occurrence (lowest edge id)
    seen = set()
    uniq = []
    for idx, (u, v) in enumerate(pred_edges):
        if (u, v) not in seen:
            seen.add((u, v))
            uniq.append((idx, u, v))
    # 2. consecutive-frame filter
    consec = [(idx, u, v) for (idx, u, v) in uniq
              if t_of.get(u) is not None and t_of.get(v) is not None
              and (t_of[v] - t_of[u]) == 1]
    # 3. merge-collapse onto the same matched GT edge, keep lowest edge id
    best = {}
    for (idx, u, v) in consec:
        mu = pred_to_gt.get(u)
        mv = pred_to_gt.get(v)
        if mu is not None and mv is not None:
            key = (mu, mv)
            if key not in best or idx < best[key][0]:
                best[key] = (idx, u, v)
    merged = []
    for (idx, u, v) in consec:
        mu = pred_to_gt.get(u)
        mv = pred_to_gt.get(v)
        if mu is not None and mv is not None:
            if best[(mu, mv)][0] == idx:
                merged.append((idx, u, v))
        else:
            merged.append((idx, u, v))
    # 4. out-degree cap: per source keep 2 lowest edge ids
    by_src = {}
    for item in merged:
        by_src.setdefault(item[1], []).append(item)
    capped = []
    for u in sorted(by_src):
        items = sorted(by_src[u], key=lambda t: t[0])[:2]
        capped.extend(items)
    return capped


def edge_counts(pred_edges, gt_edges, pred_to_gt, pred_nodes=None):
    """Sparse-aware edge TP/FP/FN per metrics.md.

    FP only when (target matched and GT target has any incoming) OR
    (source matched and GT source has any outgoing). Else ignored.
    When pred_nodes (list of {id,t,...} dicts) is given, the official S2/S3
    pred-edge pipeline runs first: exact-dedup, consecutive-frame filter,
    merge-collapse, out-degree cap. Without pred_nodes the legacy unfiltered
    path runs (backward compat; score_single always passes pred_nodes).
    Returns dict(TP,FP,FN).
    """
    if pred_nodes is not None:
        t_of = {n["id"]: int(n["t"]) for n in pred_nodes}
        edges = [(u, v) for (_, u, v) in _filter_pred_edges(
            [tuple(e) for e in pred_edges], pred_to_gt, t_of)]
    else:
        edges = [tuple(e) for e in pred_edges]
    gt_list = [tuple(e) for e in gt_edges]
    gt_set = set(gt_list)  # membership only; FN keeps GT multiplicity (official
    # uses gt_graph.num_edges(), so a duplicated GT edge counts twice)
    gt_out, gt_in = _adj(gt_list)
    # reverse index: which pred edge claims each gt edge
    claimed = set()
    TP = FP = 0
    for u, v in edges:
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
    FN = len(gt_list) - len(claimed)
    return {"TP": TP, "FP": FP, "FN": FN}


def edge_jaccard(counts):
    """Official _jaccard (S10): TP/(TP+FP+FN), NaN when the denom is 0.

    The old `1.0 if d == 0` white-sent empty samples; official returns NaN
    so summarise skips them.
    """
    d = counts["TP"] + counts["FP"] + counts["FN"]
    return counts["TP"] / d if d > 0 else float("nan")


def adjust(jaccard, T_pred, T_true, a=ADJ_A):
    """Official per_sample_metrics adjustment (S8/S10).

    Finite adjusted Jaccard only when the edge Jaccard is finite AND a
    GT-provided T_true > 0 exists. Otherwise (T_true missing/NaN/<=0, or
    edge 0/0) returns (NaN, False) and score_samples excludes the sample
    from the adjusted average — exactly like official summarise skipping
    NaN adj rows. A pred-supplied T_true is never consulted (S8).
    """
    if T_true is None or not (T_true > 0):
        return float("nan"), False
    if jaccard is None or not (jaccard == jaccard):  # NaN check, no import
        return float("nan"), False
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


def _div_window_match(pred_nodes, gt_win_nodes, voxel, max_dist):
    """Per-window full-pred vs window-GT match (S11, official match_divisions).

    Mirrors tracking_cellmot.division_metrics.match_divisions: for each GT
    division window, the FULL pred graph is matched against the window
    subgraph with the same per-timepoint DistanceMatching used by match_nodes
    (S1 primitive). Only nodes sharing a timepoint can pair. Returns
    pred_id -> gt_id for this window alone (independent of the global match
    and of every other window).
    """
    pred_by_t = {}
    for n in pred_nodes:
        pred_by_t.setdefault(int(n["t"]), []).append(n)
    gt_by_t = {}
    for n in gt_win_nodes:
        gt_by_t.setdefault(int(n["t"]), []).append(n)
    use_scipy = _HAVE_SCIPY and np is not None
    out = {}
    for t in sorted(set(pred_by_t) & set(gt_by_t)):
        P = sorted(pred_by_t[t], key=lambda d: d["id"])
        G = sorted(gt_by_t[t], key=lambda d: d["id"])
        Pc = [(n["z"], n["y"], n["x"]) for n in P]
        Gc = [(n["z"], n["y"], n["x"]) for n in G]
        if use_scipy:
            pairs = _match_group_scipy(Pc, Gc, voxel, max_dist)
        else:
            pairs = _match_group_hungarian(Pc, Gc, voxel, max_dist)
        for i, j in pairs:
            out[P[i]["id"]] = G[j]["id"]
    return out


def _div_bipartite(left, edges):
    """Maximum-cardinality bipartite matching via DFS augmenting paths.

    Mirrors official _bipartite_max_matching. left: ordered list of left ids;
    edges: dict left -> set/list of right ids. Right iteration is sorted for
    determinism (official iterates a set; cardinality is identical, this pins
    the pairing). Returns dict left -> right for matched pairs only.
    """
    match_r = {}
    match_l = {}

    def augment(u, seen):
        for v in sorted(edges.get(u, ())):
            if v in seen:
                continue
            seen.add(v)
            if v not in match_r or augment(match_r[v], seen):
                match_l[u] = v
                match_r[v] = u
                return True
        return False

    for u in left:
        augment(u, set())
    return match_l


def division_counts(pred_nodes, pred_edges, gt_nodes, gt_edges, pred_to_gt,
                    gt_to_pred, voxel=DEFAULT_VOXEL, max_dist=MAX_DIST_UM):
    """Local-window division TP/FP/FN (official mirror, AUDIT-FIX A2).

    Oracle pin: tracking_cellmot 0.1.0 @ 075fc5f5a52d11077f9dc2b074644618f26939e2
    (division_metrics.score_divisions / evaluate_divisions / match_divisions /
    extract_divisions + metrics.md "Division Jaccard").

    - S6: a GT division has EXACTLY two outgoing edges (dividing_nodes is
      out_degree == 2); a 3-child GT node is not a division. Pred forks keep
      >= 2 outgoing (any predicted node with at least two outgoing edges).
      Out-degree counts edges (duplicate edges count); successor/predecessor
      sets are unique ids.
    - S11: each GT window (parent -> divider -> children -> grandchildren) is
      rematched independently: full pred vs window subgraph with the S1
      per-timepoint assignment. The global match is NOT restricted to the
      window (the old "Known approximation" is removed).
    - S4: branch evidence uses direct-child precedence (a matched child pins
      its branch; grandchildren are fallback only when the child is
      unmatched) and unanimous-grandchild fallback (grandchildren spanning
      several GT components supply no evidence, never a picked one). No
      unordered-set first-match scan, so results never flip with id renames.
    - S5: fork poison over ALL child branches (official
      _branch_component_evidence / _pred_division_fork_sets): a locally
      merged branch (sole-parent violation) or cross-component evidence
      across two distinct branches rejects the whole fork from every pairing.
    - S7: FP "considered" class: anchor-adjacent forks (matched parent-side
      nodes and their immediate successors) that fail topology or lose the
      bipartite pairing are FPs, unioned with evaluable (matched to annotated
      GT node with outgoing) and invalid (cross-component / malformed) forks,
      minus TPs. Unmatched, valid, unevidenced forks stay ignored.
    Pairing is maximum-cardinality bipartite (one fork per GT division).
    """
    gt_by_id = {n["id"]: n for n in gt_nodes}
    pred_by_id = {n["id"]: n for n in pred_nodes}
    gt_ch = _children_map(gt_edges)
    gt_pa = _parents_map(gt_edges)
    pred_ch = _children_map(pred_edges)
    pred_pa = _parents_map(pred_edges)

    def _succ(m, u):
        return sorted(set(m.get(u, [])))

    def _pred(m, u):
        return sorted(set(m.get(u, [])))

    def _outdeg(edges, u):
        return sum(1 for (a, _b) in edges if a == u)

    pe_list = [tuple(e) for e in pred_edges]
    ge_list = [tuple(e) for e in gt_edges]
    gt_ids = [n["id"] for n in gt_nodes]
    comp = _gt_components(gt_ids, gt_edges) if gt_ids else {}

    # S6: GT == 2 outgoing edges exactly; pred >= 2.
    gt_divs = sorted([n["id"] for n in gt_nodes
                      if _outdeg(ge_list, n["id"]) == 2])
    pred_forks = sorted({p for p in pred_by_id
                         if _outdeg(pe_list, p) >= 2})

    # ---- global fork sets (official _pred_division_fork_sets on full match)
    g_p2g = dict(pred_to_gt) if pred_to_gt is not None else {}
    evaluable = {p for p in pred_forks
                 if g_p2g.get(p) is not None
                 and _outdeg(ge_list, g_p2g[p]) >= 1}
    cross_component = set()
    malformed = set()
    for p in pred_forks:
        branch_comps = []
        bad = False
        for child in _succ(pred_ch, p):
            if set(_pred(pred_pa, child)) != {p}:
                malformed.add(p)
                bad = True
                break
            if child in g_p2g and g_p2g[child] in comp:
                branch_comps.append(comp[g_p2g[child]])
                continue
            grands = _succ(pred_ch, child)
            if any(set(_pred(pred_pa, gc)) != {child} for gc in grands):
                malformed.add(p)
                bad = True
                break
            gcs = {comp[g_p2g[gc]] for gc in grands
                   if gc in g_p2g and g_p2g[gc] in comp}
            if len(gcs) == 1:
                branch_comps.append(next(iter(gcs)))
            # 0 or >=2 components -> no evidence from this branch (S4)
        if not bad and len(set(branch_comps)) >= 2:
            cross_component.add(p)
    invalid = cross_component | malformed

    # ---- per-window candidates (official score_divisions loop)
    candidates = {}
    considered = set()
    for g in gt_divs:
        children = _succ(gt_ch, g)
        if len(children) < 2:
            candidates[g] = set()
            continue
        parents = _pred(gt_pa, g)
        win_ids = ({g} | set(parents) | set(children)
                   | {gc for c in children for gc in _succ(gt_ch, c)})
        win_nodes = [gt_by_id[i] for i in win_ids if i in gt_by_id]
        w_p2g = _div_window_match(pred_nodes, win_nodes, tuple(voxel),
                                  max_dist)
        gt_parent_ids = {g} | set(parents)
        parent_ids = {pid for pid, gid in w_p2g.items()
                      if gid in gt_parent_ids}
        daughter_ids = []
        for c in children:
            lin = {c} | set(_succ(gt_ch, c))
            daughter_ids.append({pid for pid, gid in w_p2g.items()
                                 if gid in lin})
        if not parent_ids or sum(bool(s) for s in daughter_ids) < 2:
            candidates[g] = set()
            continue
        local_nodes = set(parent_ids)
        for pid in list(parent_ids):
            local_nodes.update(_succ(pred_ch, pid))
        local_forks = local_nodes & set(pred_forks)
        considered |= local_forks
        good = set()
        for f in local_forks:
            if f in invalid:
                continue
            if set([f] + _pred(pred_pa, f)).isdisjoint(parent_ids):
                continue
            pred_lineages = [{c} | set(_succ(pred_ch, c))
                             for c in _succ(pred_ch, f)]
            edges = {}
            for gi, matched in enumerate(daughter_ids):
                edges[gi] = {pi for pi, pl in enumerate(pred_lineages)
                             if not matched.isdisjoint(pl)}
            if len(_div_bipartite(list(edges), edges)) >= 2:
                good.add(f)
        candidates[g] = good

    pairing = _div_bipartite(sorted(candidates), candidates)
    tp_forks = set(pairing.values())
    TP = len(pairing)
    FN = len(gt_divs) - TP
    fp_forks = (considered | evaluable | invalid) - tp_forks
    return {"TP": TP, "FP": len(fp_forks), "FN": FN}


# ------------------------------------------------- aggregate helpers (A3)
def _expand_duplicate_ids(nodes, edges):
    """Namespace duplicate node ids to unique internal ids (S13, A3-owned).

    Official parity with csv_to_geffs.build_graph_from_rows: every node row
    stays a distinct matchable node, and edge refs to a duplicated node_id
    resolve to the LAST occurrence (dict(zip(node_id, assigned)) last-wins).
    First occurrence keeps its id (identity fast-path: no duplicates ->
    inputs returned unchanged, so all existing behavior is bit-identical);
    later occurrences get fresh ids (max-int+1.. for int ids, else
    "<id>#dup<k>" strings with full str-ification if types would mix).
    Both pred and GT sides are expanded symmetrically in score_single, so
    match_nodes/division_counts (A1/A2-owned, untouched) always see
    one-to-one-able ids: no silent match loss, no one-to-many gt_to_pred.
    Returns (nodes, edges) with unique ids.
    """
    counts = {}
    for n in nodes:
        counts[n["id"]] = counts.get(n["id"], 0) + 1
    if all(c == 1 for c in counts.values()):
        return nodes, [tuple(e) for e in edges]
    warnings.warn(
        "duplicate node ids expanded to unique internal ids "
        "(last-occurrence-wins for edge refs, official csv_to_geffs parity)",
        stacklevel=3,
    )
    all_int = all(isinstance(i, int) and not isinstance(i, bool)
                  for i in counts)
    fresh = [max([i for i in counts if isinstance(i, int)],
                 default=0) + 1] if all_int else [0]
    internal = []  # per-row internal id
    seen = {}
    for n in nodes:
        i = n["id"]
        k = seen.get(i, 0)
        seen[i] = k + 1
        if k == 0:
            internal.append(i)
        elif all_int:
            internal.append(fresh[0])
            fresh[0] += 1
        else:
            internal.append(f"{i}#dup{k}")
    if not all_int and any(not isinstance(x, str) for x in internal):
        # mixed types would break id sorting downstream: str-ify untouched
        # first-occurrences too so every internal id is a str
        strmap = {id_: str(id_) for id_ in counts}
        internal = [v if isinstance(v, str) else strmap[n["id"]]
                    for v, n in zip(internal, nodes)]
    last = {}  # original id -> LAST occurrence's internal id (official parity)
    for n, v in zip(nodes, internal):
        last[n["id"]] = v
    new_nodes = [dict(n, id=v) for n, v in zip(nodes, internal)]
    new_edges = [(last.get(u, u), last.get(v, v)) for (u, v) in
                 (tuple(e) for e in edges)]
    return new_nodes, new_edges


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
    """Score one sample. Returns dict with counts + jaccards.

    Aggregate semantics mirror official per_sample_metrics (S8/S9/S10/S13):
    T_true is GT-only (explicit override wins, pred fallback never used);
    missing T_true or zero edge events -> NaN adjusted/raw Jaccards;
    no divisions -> division NaN and score drops the 0.1 term
    (official evaluate_datasets rule); duplicate node ids are namespaced
    to unique internal ids with last-occurrence-wins edge refs (S13).
    """
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
    # S13: namespace duplicate ids (identity when unique) before A1/A2 stages
    pn, pe = _expand_duplicate_ids(pn, pe)
    gn, ge = _expand_duplicate_ids(gn, ge)
    p2g, g2p = match_nodes(pn, gn, voxel=vx, max_dist=max_dist)
    ec = edge_counts(pe, ge, p2g, pred_nodes=pn)
    ej = edge_jaccard(ec)
    T_pred = len(pn)
    # S8: T_true is GT-only (official _read_estimated_n_total reads the GT
    # geff extra; NaN/absent -> sample excluded). Pred T_true never used.
    T_true = (T_true_override if T_true_override is not None
              else gt.get("T_true"))
    adj, used_T = adjust(ej, T_pred, T_true)
    dc = division_counts(pn, pe, gn, ge, p2g, g2p, voxel=tuple(vx),
                         max_dist=max_dist)
    dd = edge_jaccard(dc)
    # S9: no divisions -> drop the term (official evaluate_datasets rule),
    # never score adj + 0.1 * 1.0.
    score = adj + DIV_W * dd if dd == dd else adj
    return {
        "adjusted_edge_jaccard": adj,
        "edge_jaccard_raw": ej,
        "division_jaccard": dd,
        "score": score,
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
    """Micro-average over samples. pairs: list of (name, pred, gt, T_true_ov).

    Mirrors official summarise (S9/S10): the adjusted edge Jaccard is
    weight-averaged (w_i = TP_i+FP_i+FN_i) over samples with FINITE adj
    only — T_true-missing and zero-count samples are skipped, never given
    weight 1; a zero total weight yields NaN (not 0.0). Division is the
    micro Jaccard over summed counts; with no divisions anywhere the term
    is dropped (division NaN + warning, score = adjusted edge only).
    Legacy toy rows keep their historical weight-1 / mean-division path.
    Returns n_adj (count of rows that fed the adjusted average).
    """
    per = []
    w_sum = 0.0
    adj_w = 0.0
    n_adj = 0
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
            n_adj += 1
            # legacy divisions have no micro counts; approximate via jaccard only
        else:
            ec = s["edge_counts"]
            w = ec["TP"] + ec["FP"] + ec["FN"]
            a = s["adjusted_edge_jaccard"]
            # S10: skip NaN-adj rows (T_true missing, zero events) exactly
            # like official summarise's adj_rows filter. w == 0 rows always
            # have NaN adj, so they contribute nothing (never weight 1).
            if a == a and w > 0:
                adj_w += a * w
                w_sum += w
                n_adj += 1
            dc = s["division_counts"]
            dTP += dc["TP"]
            dFP += dc["FP"]
            dFN += dc["FN"]
    adj_edge = adj_w / w_sum if w_sum > 0 else float("nan")
    dden = dTP + dFP + dFN
    # if all legacy, fall back to mean division jaccard
    if dden == 0 and per and all(p.get("simplified") for p in per):
        div_j = sum(p["division_jaccard"] for p in per) / len(per) if per else 0.0
    elif dden == 0:
        # S9: official drops the division term (never div_j = 1.0)
        warnings.warn(
            "No divisions present across any sample in this split; "
            "dropping division term from the combined score.",
            stacklevel=2,
        )
        div_j = float("nan")
    else:
        div_j = dTP / dden
    score = adj_edge + DIV_W * div_j if div_j == div_j else adj_edge
    return {
        "per_sample": per,
        "adjusted_edge_jaccard": adj_edge,
        "division_jaccard": div_j,
        "division_counts_sum": {"TP": dTP, "FP": dFP, "FN": dFN},
        "score": score,
        "n_adj": n_adj,
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
