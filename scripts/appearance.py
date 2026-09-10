#!/usr/bin/env python3
"""Appearance similarity for tracking links (EXP-0015, CPU-only).

Patch NCC between endpoint neighborhoods of a link, plus helpers to label
pred edges TP/FP/ignored with the exact sparse-aware rule from score.py.

Usage (library): from appearance import edge_ncc, label_edges
"""
import numpy as np

PATCH_R = (4, 10, 10)  # z,y,x half-sizes (~cell scale)


def get_patch(vol3d, z, y, x, r=PATCH_R):
    z0, z1 = max(0, z - r[0]), z + r[0] + 1
    y0, y1 = max(0, y - r[1]), y + r[1] + 1
    x0, x1 = max(0, x - r[2]), x + r[2] + 1
    return np.asarray(vol3d[z0:z1, y0:y1, x0:x1], dtype=np.float32)


def ncc(a, b):
    a = a.ravel().astype(np.float64)
    b = b.ravel().astype(np.float64)
    n = min(a.size, b.size)
    a, b = a[:n], b[:n]
    sa, sb = a.std(), b.std()
    if sa < 1e-9 or sb < 1e-9:
        return 0.0
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))


def label_edges(pred_nodes, pred_edges, gt_nodes, gt_edges,
                voxel=(1.625, 0.40625, 0.40625), max_dist=7.0):
    """Mirror score.py: per-t optimal match, then TP / FP / ignored per edge.
    Returns (labels, match_info). labels: {idx: 'TP'|'FP'|'ignored'}."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    from score import match_nodes
    p2g, _ = match_nodes(pred_nodes, gt_nodes, voxel=voxel, max_dist=max_dist)
    gt_set = {(a, b) for a, b in map(tuple, gt_edges)}
    out, inn = {}, {}
    for a, b in map(tuple, gt_edges):
        out.setdefault(a, set()).add(b)
        inn.setdefault(b, set()).add(a)
    labels = {}
    for i, (u, v) in enumerate(map(tuple, pred_edges)):
        mu, mv = p2g.get(u), p2g.get(v)
        if mu is not None and mv is not None and (mu, mv) in gt_set:
            labels[i] = "TP"
        elif (mv is not None and len(inn.get(mv, ())) > 0) or \
                (mu is not None and len(out.get(mu, ())) > 0):
            labels[i] = "FP"
        else:
            labels[i] = "ignored"
    return labels, p2g
