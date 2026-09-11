# EXP-0041 — Window-best full-video validation (0b24845f@98.5 / 0c582fdc@97.5)

## Hypothesis

Full-video detection at the EXP-0024 window-best (t20–29) levels —
44b6_0b24845f @ 98.5 and 44b6_0c582fdc @ 97.5 — transfers to full video:
per-sample full-video recall stays within 0.10 of window recall AND full-video
adjusted edge jaccard stays within 0.10 of the best full-video adj so far for
that sample. Falsifiable by the criteria below.

## Background

- PROTOCOL v1.1 (frozen): score = adjusted_edge_jaccard + 0.1*division_jaccard;
  node match 7 µm; voxel z=1.625 / y=x=0.40625; trusted scorer scripts/score.py
  v1.1.0. Detector CLI defaults = frozen DoG (1,3,3)/(1.6,5,5), min-size 50,
  percentile, downsample 1. Linker = baseline_link defaults (gate 7 µm).
- Window refs (EXP-0024, t20–29, read from metrics.json): 0b24845f@98.5
  recall 0.80 (8/10); 0c582fdc@97.5 recall 0.50 (5/10).
- Full-video context (EXP-0040, read from metrics.json): 0b24845f @99.0
  rec 0.325 / @96.0 rec 0.40, adj 0.1872 @96.0; 0c582fdc @99.0 rec 0.197 /
  @96.0 rec 0.41, adj 0.1874 @96.0. Window-best levels themselves never tested
  full-video by the EXP-0040 lineage (see notes.md for the EXP-0034 caveat).

## Falsification criteria

- Per sample HOLDS iff (window_recall − full_recall) ≤ 0.10 AND
  (bar_adj − full_adj) ≤ 0.10, where bar_adj = freshly rescored (never pasted)
  best full-video adj so far (EXP-0040 @96.0 preds rescored with score.py CLI).
- Overall: 2/2 HOLDS → GO (window-best levels viable; recommend per-sample
  policy rung, do not run); else STOP.
