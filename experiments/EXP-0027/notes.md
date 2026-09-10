# Notes — EXP-0027 Detection-internals profile

## Log
- Created via scripts/new_experiment.sh.
- Ran ./experiments/EXP-0027/run.sh (~1 min, CPU-only). All 10 frames pass the
  fidelity gate: staged node list identical to DD.detect(), thr match <1e-3,
  staged total within ~0.03 s of whole-function time. scripts/* untouched.

## Decisions
- pct=98.5 per mission brief (differs from dog_detect.py CLI default 99.5 — flagged, not changed).
- `subtract` (dog = g_small - g_large) timed separately for completeness; folded
  narrative keeps the 8 mission stages (cast, gauss-small, gauss-large, percentile,
  label, bincount, moments/means, split-skipped=0.0).
- `label` stage = threshold compare + scipy label() together.
- Projections are arithmetic (measured pass costs), no prototype implemented per mission.

## Key evidence (means over t=20..24)
- dense 6bba_05b6850b: 0.81 s/f staged (whole 0.80) — moments/means 0.470 s (58.1%),
  gauss_small 0.115 (14.2%), gauss_large 0.148 (18.3%), bincount 0.030 (3.7%),
  label 0.019 (2.3%), percentile 0.011 (1.3%), rest ~2%. n_comp=48, kept~43.
- sparse-ish 44b6_0113de3b: 2.18 s/f staged (whole 2.15) — moments/means 1.850 s
  (84.8%), gaussians 0.253 (11.6%), bincount 0.029 (1.3%), percentile 0.021 (1.0%),
  label 0.020 (0.9%). n_comp=193, kept~170-181.
- Sub-split (1 frame/video): argwhere loop = ~100% of moments/means (mean() ~1 ms);
  ~10.1-10.3 ms per component per full-volume (4M-voxel) scan — O(C*N) confirmed
  linear in component count (0.47 s @48 comps vs 1.85 s @193 comps).
- Naming note: "dense/sparse" tags follow the mission brief; at pct=98.5 the 6bba
  frames yield ~43 nodes vs ~170-181 for 44b6 — cost tracks component count, not the tag.

## Paydown ranking (projected per-frame saving)
1. Vectorized centroids (single-pass bincount/center_of_mass replacing per-component
   argwhere; conservative cost 0.12 s/f from measured pass costs): dense 0.35 s/f
   (43%), sparse 1.73 s/f (79%). TOP — quality-neutral (identical means).
2. Footprint-truncated gaussians (truncate 4.0->2.0, ~45% off each gauss):
   dense 0.12 s/f (15%), sparse 0.11 s/f (5%). Second; needs quality check.
3. Drop large-gauss (single-scale): dense 0.15 s/f (18%), sparse 0.14 s/f (7%) —
   quality risk, listed only.
4. Percentile subsampling x8: dense 0.009 s/f (1.2%), sparse 0.019 s/f (0.9%) —
   not worth it (percentile already ~1%).
