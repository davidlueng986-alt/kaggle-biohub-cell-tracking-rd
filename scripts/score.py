#!/usr/bin/env python3
"""Trusted scorer (SIMPLIFIED dry-run capable) for BioHub cell-tracking.

Full metric spec:
  https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md

Competition score = adjusted_edge_jaccard + 0.1 * division_jaccard
with 7um spatial matching tolerance, sparse-aware evaluation,
T_true penalty, and division local-window scoring.

STATUS: SIMPLIFIED — suitable for pipeline smoke tests and EXP-0001 wiring.
TODO(full geff matching): replace `_jaccard` / `_division_jaccard` with the
  exact geff-based edge matching (7um tolerance), sparse-aware masking,
  T_true penalty, and division local-window logic from metrics.md.
  Stage 3 (EXP-0001) must swap in the full implementation and freeze it
  in docs/PROTOCOL.md before trusting LB-gating decisions.

Usage:
  python3 scripts/score.py --dry-run
  python3 scripts/score.py --pred pred.json --gt gt.json [--out metrics.json]

File format (JSON, stdlib only):
  {"edges": [[u, v], ...], "divisions": [[parent, d1, d2], ...]}
  Edges/divisions are ID tuples. Division entries optional (default []).
"""

import argparse
import json
import sys


def _jaccard(pred_edges, gt_edges):
    """SIMPLIFIED adjusted_edge_jaccard: plain set Jaccard over edge tuples.

    TODO(geff-matching): implement 7um spatial matching + sparse-aware mask
    + T_true penalty per metrics.md instead of exact ID-tuple overlap.
    """
    p = {tuple(sorted(e)) for e in (pred_edges or [])}
    g = {tuple(sorted(e)) for e in (gt_edges or [])}
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    return len(p & g) / len(p | g)


def _division_jaccard(pred_divs, gt_divs):
    """SIMPLIFIED division_jaccard: plain set Jaccard over division tuples.

    TODO(division-window): implement local temporal window matching per
    metrics.md instead of exact tuple overlap.
    """
    p = {tuple(d) for d in (pred_divs or [])}
    g = {tuple(d) for d in (gt_divs or [])}
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    return len(p & g) / len(p | g)


def score_dict(pred, gt):
    edge_j = _jaccard(pred.get("edges"), gt.get("edges"))
    div_j = _division_jaccard(pred.get("divisions"), gt.get("divisions"))
    total = edge_j + 0.1 * div_j
    return {
        "adjusted_edge_jaccard_simplified": edge_j,
        "division_jaccard_simplified": div_j,
        "score_simplified": total,
        "simplified": True,
        "metric_spec": "https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md",
    }


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description="SIMPLIFIED BioHub tracking scorer")
    ap.add_argument("--pred", help="Path to pred JSON")
    ap.add_argument("--gt", help="Path to gt JSON")
    ap.add_argument("--out", help="Optional path to write metrics JSON")
    ap.add_argument("--dry-run", action="store_true",
                    help="Run toy example (no input files needed)")
    args = ap.parse_args(argv)

    if args.dry_run:
        pred = {"edges": [[1, 2], [2, 3], [3, 4]],
                "divisions": [[1, 2, 3]]}
        gt = {"edges": [[1, 2], [2, 3], [4, 5]],
              "divisions": [[1, 2, 3]]}
        result = score_dict(pred, gt)
        print(json.dumps(result, indent=2))
        print("dry-run OK (SIMPLIFIED scorer; see TODO in header)", flush=True)
        return 0

    if not args.pred or not args.gt:
        ap.error("provide --pred and --gt, or use --dry-run")
    pred = load_json(args.pred)
    gt = load_json(args.gt)
    result = score_dict(pred, gt)
    print(json.dumps(result, indent=2))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)
        print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
