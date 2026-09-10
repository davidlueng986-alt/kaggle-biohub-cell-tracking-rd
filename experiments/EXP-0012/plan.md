# Plan — EXP-0012 Splitter full-video

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Sample: `6bba_05b6850b` only (dense; 44b6 locked @99.0 base, sparse,
  splitter unneeded). All 100 frames @98.0 + `--split-size 3000`.
- Link `baseline_link` (causal Hungarian). Score vs full GT, true T_true.
- Bars: EXP-0009 @98.5 row (recall 0.893, raw 0.7989, adj 0.8194).

## Cold-run steps

1. `bash experiments/EXP-0012/run.sh` → `metrics.json` + verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~8 min (100 frames with split overhead + linking/scoring).
