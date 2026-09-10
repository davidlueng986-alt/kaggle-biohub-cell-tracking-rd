# Plan — EXP-0014 Scale fusion window gate

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Sample `6bba_05b6850b`, blocks t20–29 + t40–49 (same gate window).
- Configs: A baseσ@98.5 | B smallσ@98.5 | C smallσ@98.0 |
  D A∪novel-B (NMS 3 µm) | E A∪novel-small@98.0 (NMS 3 µm).
- Readouts: recall, counts, linked-block edge raw/adj vs GT subgraph.

## Cold-run steps

1. `bash experiments/EXP-0014/run.sh` → `metrics.json` + GO/STOP verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~5 min (100 frame-detections + link/score). 1 sample, 20 frames.
