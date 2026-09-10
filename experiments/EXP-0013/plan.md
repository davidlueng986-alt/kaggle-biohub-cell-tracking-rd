# Plan — EXP-0013 Window gate with edge readout

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Sample: `6bba_05b6850b` (dense; splitter irrelevant on sparse 44b6).
  Blocks: t20–29 + t40–49 (20 contiguous-linkable frames spanning density
  regimes incl. miss frames 42,43,44 — the EXP-0011/0012 lesson).
- Configs: A @98.5 base | B @98.0+split | C B+prom0.7 | D C+phased-link.
  (split-size 3000, footprint (5,15,15) frozen from EXP-0012.)
- Readouts per config: recall, det counts, linked-block edge (raw + adj)
  vs GT subgraph (T_true ×20/100, labeled approx; raw primary).

## Cold-run steps

1. `bash experiments/EXP-0013/run.sh` → `metrics.json` + GO/STOP verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~5 min (80 frame-detections + link/score). 1 sample, 20 frames.
