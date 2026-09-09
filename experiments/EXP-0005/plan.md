# Plan — EXP-0005 Radius ablation + isolation gate

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Grid: propose-um ∈ {9, 10, 11, 12} × isolation {off} + isolation {on} at
  r=10 and r=15 (veto probe; r=15-off reuses EXP-0004 numbers by reference).
  Base links + GT graphs from EXP-0003. Floor: EXP-0003 metrics.
- Selection: (1) sub-gate pass (div gain + no edge regression both folds),
  (2) worst-fold micro-edge, (3) smallest radius on ties (conservative).

## Cold-run steps

1. `bash experiments/EXP-0005/run.sh` — links + scores grid, writes
   `metrics.json` with ablation table, selection, verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, minutes (graph ops; 6 samples × 6 configs).
