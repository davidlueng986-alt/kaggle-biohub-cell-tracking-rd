# Plan — EXP-0009 Full-video @98.5

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Samples: `44b6_0113de3b` + `6bba_05b6850b`, all 100 frames, pct 98.5.
- Detector `scripts/dog_detect.py` (frozen DoG params, only pct changes).
- Link `baseline_link` (causal Hungarian; scipy fast path dense).
- Score vs full GT with true T_true; compare raw + adjusted vs EXP-0008
  @99.0 rows (same samples, same linker — pure threshold effect).

## Cold-run steps

1. `bash experiments/EXP-0009/run.sh` → `metrics.json` + tradeoff table.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~10 min (200 frame-detections + linking/scoring). 2 subset
  samples only.
