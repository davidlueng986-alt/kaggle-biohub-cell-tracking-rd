# Plan — EXP-0045 H-003 residual: detection gate vs linking opportunity

## Config / seeds
Deterministic, CPU-only, no randomness. Trusted imports only:
`match_nodes`, `_um_dist`, `DEFAULT_VOXEL=(1.625,0.40625,0.40625)`,
`max_dist=7.0` from scripts/score.py v1.1.0 (read-only, not edited).

## Steps
1. GT divisions: nodes with >= 2 outgoing GT edges (computed, not assumed):
   6bba_05db0fb1 -> 25000381, 53001011, 63001217; 6bba_062c8d37 -> 90001276.
2. Run `./experiments/EXP-0045/run.sh` (~90 s; per-t Hungarian over full-video
   graphs). It matches EXP-0021 preds vs EXP-0003 GT via `match_nodes`,
   records per-division matched ids, nearest-detected distances, GT vs
   detected daughter distances, fork edges from matched parent, and site
   edges, then classifies (all present + forked = RECOVERED; all present but
   unlinked = LOST-AT-LINKING; else LOST-AT-DETECTION) and writes
   metrics.json with verdict GO iff >= 1 LOST-AT-LINKING.
3. Cold rerun: `chmod +x experiments/EXP-0045/run.sh && ./experiments/EXP-0045/run.sh`.

## Budget
CPU-only, ~2 min single run. No GPU, no pip installs, no Kaggle calls.
