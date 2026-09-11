# Plan — EXP-0051 GT-motion regime test for gate-10 advantage (analysis-only)

## Config / seeds
- Deterministic, CPU-only, < 20 min. No seeds, no randomness.
- Deps: stdlib + numpy only (percentiles match numpy linear interp).
- Inputs (READ-only, never written): experiments/EXP-0003/gt/<sid>_gt.json
  (all 6), experiments/EXP-0050/metrics.json (frozen IMAGE gate deltas),
  experiments/EXP-0017/grid.json (frozen ORACLE arm1 gate rows).
- Voxel scale fixed: dz=1.625, dy=dx=0.40625 um/voxel. All GT edges span dt=1
  (verified in-run; assert fails otherwise).
- Output: experiments/EXP-0051/metrics.json only (plus this plan / hypothesis /
  notes / run.sh). No detection, no linking, no scorer reruns.

## Steps
1. Run `bash experiments/EXP-0051/run.sh` — it:
   a. Loads each GT graph, maps id->node, computes scaled Euclidean displacement
      per GT edge; records n_nodes, n_edges, occupied-frame count, density =
      n_nodes/n_occupied_frames, frac(7,10] = mean(7<d<=10), median, p90, max.
   b. Reads IMAGE gate10-minus-gate7 adj per sample = -delta_adj_g7_minus_g10
      from EXP-0050/metrics.json; reads ORACLE gate10-minus-gate7 adj per sample
      = grid arm1 "10.0".edge − arm1 "7.0".edge from EXP-0017/grid.json.
   c. Hand-rolled Spearman (average-rank ties, rank 1 = largest value) for
      fast-fraction vs IMAGE advantage (primary), density vs IMAGE advantage,
      fast-fraction vs ORACLE advantage, p90 vs ORACLE (diagnostic).
   d. Applies verdict rule (rho_image_fast >= 0.8 → STRONG-MECHANISM else WEAK)
      and rewrites metrics.json with the full table + rhos + verdict.
2. Verify: re-run is bit-identical (diff metrics.json before/after); check the
   killer row (0c582fdc frac=0 vs top IMAGE advantage) by eye.
3. No LB, no promotion, no follow-up runs from this EXP.

## Budget
CPU-only analysis, seconds (< 1 min). No GPU, no Kaggle, no pip installs.
