# Plan — EXP-0036 Drift audit

## Config / seeds

- Deterministic. Extract notebook code cells, exec in isolation with stub
  constants; compare vs repo `dog_detect`/`baseline_link`/`graphs_to_csv`
  on 6bba t20–22 @98.5 + 44b6 t20–22 @99.0 (positions), 3-frame chains
  (edges, incl. scipy path at N=70), synthetic graph (writer bytes).

## Cold-run steps

1. `bash experiments/EXP-0036/run.sh` → `metrics.json` (equality table).
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~5 min. No network, no Kaggle calls.
