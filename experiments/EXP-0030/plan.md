# Plan — EXP-0030 Min-size ablation

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic, CPU-only.
- Sample: `6bba_05b6850b` (dense; same gate window as EXP-0013/14/16).
  Blocks: t20–29 + t40–49 (20 contiguous-linkable frames).
- Configs (all @98.5, default sigmas, no split): ms25 / ms50 (=A reference,
  recomputed, never pasted) / ms100.
- Readouts per config: per-frame recall + det counts, linked-block edge
  (raw + adj) vs GT subgraph (T_true ×20/100, labeled approx; raw primary).

## Cold-run steps

1. `bash experiments/EXP-0030/run.sh` → 60 frame-detections + link/score →
   `metrics.json` + GO/STOP verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~2–4 min (60 frame-detections + link/score). 1 sample, 20 frames.
