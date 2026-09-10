# Plan — EXP-0016 Soft-weight window gate

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Sample `6bba_05b6850b`, blocks t20–29 + t40–49, @98.5 detections reused
  from EXP-0013 (`A_t*.json` — frozen, no re-detection).
- Grid W ∈ {0, 1, 2, 4} via `appearance.link_weighted` (zarr reads cached).
  GT subgraph + T scaling as in EXP-0013.

## Cold-run steps

1. `bash experiments/EXP-0016/run.sh` → `metrics.json` + GO/STOP verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~10 min (NCC over gated pairs × 4 W + link/score). 1 sample.
