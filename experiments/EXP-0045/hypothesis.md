# EXP-0045 — H-003 residual: detection gate vs linking opportunity at 4 GT divisions

## Hypothesis
On IMAGE graphs (EXP-0021 preds), GT divisions fail to recover because the
linker cannot emit forks even when parent + both daughters are all detected
within the 7 um gate — i.e. at least one of the 4 GT divisions in
6bba_05db0fb1 (3 divs) / 6bba_062c8d37 (1 div) classifies as LOST-AT-LINKING
(all of p/d1/d2 matched by `match_nodes`, but no fork edges from the matched
parent). Falsified if ALL 4 classify as LOST-AT-DETECTION.

## Background
- H-003 residual: EXP-0044 r10 forks on IMAGE graphs bought 0 TP + 35 FPs;
  EXP-0005 r10 worked only on ORACLE graphs. Open: detection gate or linking?
- PROTOCOL v1.1 frozen: score = adjusted_edge_jaccard + 0.1*division_jaccard;
  node match 7 um per-timepoint optimal assignment, voxel z=1.625/y=x=0.40625;
  scorer scripts/score.py v1.1.0.
- GT: experiments/EXP-0003/gt/6bba_05db0fb1_gt.json (3 divs),
  6bba_062c8d37_gt.json (1 div). Preds: experiments/EXP-0021/<sid>_pred.json.

## Falsification criteria
- GO (linking-side headroom) iff >= 1 division is LOST-AT-LINKING.
- STOP (detection-only gap) iff all 4 are LOST-AT-DETECTION.
- Result: 1 LOST-AT-LINKING (6bba_062c8d37:90001276) -> GO (see metrics.json).
