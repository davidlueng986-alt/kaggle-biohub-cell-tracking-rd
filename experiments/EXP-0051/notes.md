# Notes — EXP-0051 GT-motion regime test for gate-10 advantage (analysis-only)

## Log
- Created via scripts/new_experiment.sh (EXP-0051 verified FREE via ls).
- Analysis-only: GT-motion stats from experiments/EXP-0003/gt (all 6) +
  frozen deltas (EXP-0050/metrics.json IMAGE, EXP-0017/grid.json ORACLE).
  No detection/linking reruns, no scorer reruns, no pip installs.
- `bash experiments/EXP-0051/run.sh` reproduces metrics.json bit-identically
  (re-ran once to verify; verdict WEAK, rho_image_fast=-0.3769).

## Outcome: WEAK (flips NOT explained by GT fast-cell fraction)
Rank table (rank 1 = largest; ties averaged; order
0113de3b, 0b24845f, 0c582fdc, 05b6850b, 05db0fb1, 062c8d37):
- fast (7,10] frac: 0.0200, 0.0000, 0.0000, 0.0059, 0.0169, 0.0290
  → ranks 2.0, 5.5, 5.5, 4.0, 3.0, 1.0
- IMAGE g10−g7 adj: −0.2777, −0.0020, +0.0258, −0.0060, −0.0171, +0.0131
  → ranks 6.0, 3.0, 1.0, 4.0, 5.0, 2.0
- ORACLE g10−g7 adj: +0.0220, 0.0, 0.0, +0.0064, +0.0158, +0.0314
  → ranks 2.0, 5.5, 5.5, 4.0, 3.0, 1.0 (== fast ranks exactly)
- Spearman: fast-vs-IMAGE −0.377; density-vs-IMAGE −0.116; fast-vs-ORACLE
  +1.000; p90-vs-ORACLE +0.754.
- Killer counterexample: 44b6_0c582fdc has 0/70 GT edges in (7,10] (max 5.03 um)
  yet the LARGEST IMAGE gate-10 win (+0.0258: 7/7/63 → 9/8/61). Conversely
  44b6_0113de3b has the 2nd-highest fast fraction (1/50, 0.02) yet the largest
  gate-10 LOSS (−0.2777: FP 2→16). Density fails too (sparse 0c582fdc wins for
  g10 while sparse 0113de3b collapses under g10).
- Interpretation: mechanism (gate-10 recovers genuine 7–10 um moves) is REAL on
  clean ORACLE graphs (rho=1.0) but NOT predictive on IMAGE graphs, where the
  TP-gain-vs-FP-cost balance is set by detection noise/clutter, not GT motion.
  The two IMAGE flips look idiosyncratic at n=6.

## Decisions
- Verdict WEAK → keep uniform gate-7; do NOT pursue per-regime gate rung.
- No promotion, no LB action from this EXP. Future gate work (if any) needs an
  image-measurable selector (e.g. detected-graph density/motion), not GT motion.

## Next-stage input
- Verdict WEAK (fast-vs-IMAGE rho=−0.377 < 0.8; density-vs-IMAGE rho=−0.116;
  fast-vs-ORACLE rho=+1.000 diagnostic). Numbers for RESULTS/STATE in
  metrics.json (gt_stats + spearman + verdict).
