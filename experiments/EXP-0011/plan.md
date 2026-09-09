# Plan — EXP-0011 Full-video 6bba@98.0

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Sample: `6bba_05b6850b` only, all 100 frames, pct 98.0. Detector
  `scripts/dog_detect.py` (frozen DoG params). Link `baseline_link`
  (causal Hungarian). Score vs full GT, true T_true.
- Reference: EXP-0009 6bba@98.5 row (recall 0.893, raw 0.7989, adj 0.8194).
  44b6 arm untouched (locked @99.0, EXP-0008 artifact).

## Cold-run steps

1. `bash experiments/EXP-0011/run.sh` → `metrics.json` + verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~5 min (100 frame-detections + linking/scoring). 1 subset
  sample only.
