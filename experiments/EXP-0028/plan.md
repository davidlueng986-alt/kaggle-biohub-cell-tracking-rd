# Plan — EXP-0028 Fidelity gate + adopt

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Code change: `scripts/dog_detect.py` vectorized centroids when
  `split_size is None` (split path keeps legacy loop — verified working).
- Fidelity set: 6bba t20–29+t40–49 @98.5 (expect = EXP-0013 A_t files,
  position equality) + 44b6_0113de3b t20–29 @99.0 (expect = EXP-0008
  full_t files). Linked window edge must equal 143/2/5.
- Timing: old elapsed_s from frozen files vs new measured.

## Cold-run steps

1. `bash experiments/EXP-0028/run.sh` → `metrics.json` + adopt/revert verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~5 min (50 frames detect ×2 code paths? No — new code only,
  compared against frozen artifacts; legacy loop retained only in split path).
