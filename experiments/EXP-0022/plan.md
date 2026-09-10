# Plan — EXP-0022 Downsample parity + timing

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Sample `6bba_05b6850b` (dense; timing matters most where detections are
  many — plus 44b6_0113de3b control for the timing contrast).
  Blocks t20–29 + t40–49 (same gate window).
- Configs: A @98.5 full-res (anchor: must equal EXP-0013 A exactly) vs DS
  @98.5 half-res y/x (centroids ×2, no refine v1).
- Readouts: recall, counts, linked-block edge raw/adj vs GT subgraph,
  s/frame both configs.

## Cold-run steps

1. `bash experiments/EXP-0022/run.sh` → `metrics.json` + GO/STOP verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~5 min (40 frame-detections ×2 configs + link/score, 1–2 samples).
