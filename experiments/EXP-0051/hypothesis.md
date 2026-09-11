# EXP-0051 — GT-motion regime test for gate-10 advantage (analysis-only)

## Hypothesis
The IMAGE-graph gate-10 advantage (gate10-minus-gate7 adjusted edge Jaccard per
sample, EXP-0050) is rank-explained by the GT fast-cell fraction — the share of
GT edge displacements in the (7,10] um band (voxel-scaled z=1.625/y=x=0.40625).
If so, a per-regime gate has a principled GT-motion selector worth a future
gated rung; if not, the two IMAGE flips are idiosyncratic.

## Background
- Established (RESULTS rows EXP-0017/EXP-0050, verified by reading their
  metrics.json + grid.json, not recomputed): IMAGE gate-7 beats gate-10 on 4/6
  (0113de3b +0.2777; 05b6850b +0.0060; 0b24845f +0.0020; 05db0fb1 +0.0171 adj,
  g7-minus-g10) but gate-10 flips 0c582fdc (+0.0258) and 062c8d37 (+0.0131 adj,
  g10-minus-g7). ORACLE gate-10 wins everywhere (EXP-0018 PROMOTED).
- Mechanism hypothesis under test: gate-10 recovers genuine 7–10 um
  displacements; net win iff TP gain beats FP cost — regime-dependent.
- GT: experiments/EXP-0003/gt/<sid>_gt.json (all 6). Frozen deltas reused from
  experiments/EXP-0050/metrics.json (image) + experiments/EXP-0017/grid.json
  (oracle arm1 gate rows). No new detection/linking in this EXP.

## Falsification criteria
Compute per-sample GT-motion descriptors (no detection) and hand-rolled
Spearman (average-rank ties) of descriptor rank vs gate-10-advantage rank.
STRONG-MECHANISM iff rho >= 0.8 on the IMAGE advantage (fast fraction or
density orders the flips); else WEAK (keep uniform gate-7, no per-regime rung).

## Result
WEAK: fast-fraction vs IMAGE-advantage rho = -0.377 (density vs IMAGE rho =
-0.116). Killer counterexample 44b6_0c582fdc has 0/70 fast GT edges yet the
largest IMAGE gate-10 win (+0.0258). Oracle arm is perfectly ordered
(rho = 1.000) — mechanism real on clean graphs, not predictive on IMAGE graphs.
