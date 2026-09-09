# Plan — EXP-0010 Combo + window probe

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Combo arms (frozen artifacts, re-scored for ledger cleanliness):
  44b6_0113de3b←EXP-0008 `full_44b6_0113de3b_pred.json` (@99.0),
  6bba_05b6850b←EXP-0009 `full_6bba_05b6850b_pred.json` (@98.5).
- Uniform references: @99.0 both (EXP-0008 rows), @98.5 both (EXP-0009 rows).
- Window probe: 6bba t0–9 @98.0 → recall/counts (10 frames, ~15 s).

## Cold-run steps

1. `bash experiments/EXP-0010/run.sh` → `metrics.json` (combo table,
   window probe, verdict).
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~1 min (re-scores + 10 frame-detections). No new full videos.
