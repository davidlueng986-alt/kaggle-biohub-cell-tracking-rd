# EXP-0039 — 05db0fb1 full-video @96.0 recall-vs-count-cost test

## Hypothesis

Lowering the DoG detection percentile from 98.5 to 96.0 on the full 100-frame
6bba_05db0fb1 video raises node recall enough (≈0.61 window prior, t20–29)
that the adjusted edge jaccard INCREASES despite the count-cost of extra
detections — because the scorer's sparse-aware FP rule ignores detections in
empty regions while extra true matches create edge TPs.

## Background

- PROTOCOL v1.1 (frozen): score = adjusted_edge_jaccard + 0.1*division_jaccard;
  node match 7 um; voxel z=1.625/y=x=0.40625; trusted scorer scripts/score.py
  v1.1.0.
- Prior: 05db0fb1 window t20–29 recall 0.615 @96.0 vs 0.41 @97.5 (monotone
  rising, T_ratio ≈0.65, timing flat).
- Baseline: full-video @98.5 (EXP-0021 row): recall 0.290, raw 0.1969,
  adj 0.2092, ec 251/92/932, div 0.0 (3 GT divisions, one-to-one linker
  predicts zero forks).
- GT: experiments/EXP-0003/gt/6bba_05db0fb1_gt.json (T_true=69800).

## Falsification criteria

- GO: full-video recall(@96.0) > recall(@98.5) AND adj(@96.0) > adj(@98.5).
- MIXED: recall up but adj down (count cost wins).
- FAIL: both down.
- Baseline recomputed by fresh re-scoring (never pasted); deltas recorded in
  metrics.json.
