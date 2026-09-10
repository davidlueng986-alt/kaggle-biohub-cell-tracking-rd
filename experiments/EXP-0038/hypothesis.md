# EXP-0038 — T-discipline track filter

## Hypothesis

Applying the reference-style T-discipline post-filter (drop tracks with
frame-length < 6, prune isolated single nodes, frac-capped rescue at 5% of
kept nodes) to our frozen unfiltered dense pred graphs raises the
PROTOCOL v1.1 adjusted edge Jaccard by >= +0.02 on BOTH samples
(6bba_05b6850b from EXP-0009, 6bba_05db0fb1 from EXP-0021) while losing
<= 0.005 GT-node recall and reducing sparse-aware FP.

Rationale: under PROTOCOL v1.1 the sparse-GT FP rules + T_true penalty
(a=0.1) punish unfiltered dense output (COMPETITION.md pitfall 3); the
same-account Lineage Forge reference (0.946 vs our 0.650) uses exactly
min-track-len 6 + prune-isolated + frac-capped rescue, so short tracks in
dense graphs should be predominantly FP junk.

## Background

- `docs/COMPETITION.md` pitfall 3 (count discipline); PROTOCOL v1.1 metric
  `score = adjusted_edge_jaccard + 0.1*division_jaccard` (`scripts/score.py`
  v1.1.0, `a=0.1`, sparse-aware FP cases, per-sample weighting).
- Frozen inputs (reuse only, no re-detect/re-link):
  `experiments/EXP-0009/full_6bba_05b6850b_pred.json`
  (@98.5: raw 0.7989 adj 0.8194, ec 699/30/146),
  `experiments/EXP-0021/6bba_05db0fb1_pred.json`
  (@98.5: raw ~0.197 adj ~0.209);
  GT `experiments/EXP-0003/gt/6bba_05b6850b_gt.json` (T_true=6362),
  `6bba_05db0fb1_gt.json` (T_true=69800).

## Falsification criteria

Gate (worst-of-2): adj gain >= +0.02 AND GT-node recall loss <= 0.005
(recall = `match_nodes` GT matched fraction; edge-TP loss <= 1% as
cross-check) AND FP down on both samples. Else FAIL → park filtering
(verdict STOP). Result: FAIL on all three sub-bars (see notes.md).
