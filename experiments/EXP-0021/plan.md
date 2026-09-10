# Plan — EXP-0021 Transfer across subset

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Levels: 44b6 → pct 99.0; 6bba → pct 98.5 (per-embryo policy, EXP-0010).
- Reuse (verified): 44b6_0113de3b ← EXP-0008 full-video det files;
  6bba_05b6850b ← EXP-0009 full-video det files. Spot re-detect t=25 of
  each and assert byte-equality before reuse.
- Fresh: 44b6_0b24845f, 44b6_0c582fdc @99.0; 6bba_05db0fb1, 6bba_062c8d37
  @98.5 (400 frames).
- Link with global re-id (`baseline_link`, causal Hungarian); score vs
  full GT, true T_true; embryo micros + worst-fold.

## Cold-run steps

1. `bash experiments/EXP-0021/run.sh` → `metrics.json` + transfer verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~15 min (400 fresh frame-detections + 6 link/score).
