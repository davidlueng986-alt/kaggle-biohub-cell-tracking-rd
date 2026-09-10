# Notes — EXP-0028 Vectorized centroids (H-005)

## Log
- 2026-09-10: `bash experiments/EXP-0028/run.sh` → exit 0, ADOPTED.
- Fidelity: 0/30 mismatched frames (6bba t20–29+t40–49 + 44b6 t20–29 vs
  frozen EXP-0013/EXP-0008 artifacts, position equality); linked window
  edge exactly 143/2/5. `center_of_mass` uniform weights == argwhere means
  bit-for-bit on this data (no .5-rounding collisions in 30 frames).
- Timing: 1.93× overall mixed-density (old/new elapsed sums over the same
  30 frames). Below EXP-0027's 43%/79% projections (gaussian+label share
  grows as moments shrink — projections assumed all-else-fixed shares;
  recorded correction). 6bba-only slice ~1.3×, 44b6 slice ~3× (sparse
  frames had the most loop overhead per detection).
- Split path keeps the legacy loop (verified functional post-edit:
  6 splits on t25 probe) — vectorization applies iff `split_size is None`.
- LB check 2026-09-10: all submit refs still PENDING (no diagnostic yet).

## Decisions
- `keep-trying` — ADOPTED into `scripts/dog_detect.py` (strictly better,
  zero quality change). Infra rung: no metric movement by design.
- H-005 status: detection ~1.93× cheaper (6bba 0.85→~0.64 s/f, 44b6
  2.05→~0.7 s/f → per-video ~64 s + ~70 s → hidden projection improves but
  stays tight vs 12 h; next paydown: truncated gaussians (EXP-0027
  runner-up, pending quality check) or frame-mask ideas that survive dense
  tissue (ROI did not).
- Next: EXP-0029 kernel upgrade (vectorized detector + DS-switch audit) or
  truncated-gaussian probe — PM's call on submit timing (2 slots left).
