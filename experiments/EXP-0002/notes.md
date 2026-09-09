# Notes — EXP-0002 Full-scorer geometric validation

## Log
- 2026-09-09: scaffolded via `scripts/new_experiment.sh EXP-0002`.
- 2026-09-09: `bash experiments/EXP-0002/run.sh` → exit 0; all 6 falsification checks pass.
- Results (v1.1 scorer, geometric toy, no real data):
  - fold0_perfect (44b6 stand-in, 3-chain): score **1.1** (edge 1.0, div 1.0-empty).
  - fold0_idswitch (wrong edge 1→3): score **0.333**, FP ≥ 1 — trap penalised.
  - fold0_inflated (2× nodes, T_true=3 pinned): adjusted **0.9** vs 1.0 — penalty works (factor 0.9).
  - fold1_perfect (division probe): score **1.1**, division TP=1.
  - fold1_nodiv (dropped branch): division FN ≥ 1.
- `bash scripts/run_loop.sh --dry-run` → exit 0 (validates EXP-0000/0001/0002).

## Decisions
- `keep-trying` — geometric path validated but no real data; NOT promotable (no embryo-CV on zarr/.geff). Next: EXP-0003 real embryo-CV baseline after competition Rules acceptance + `kaggle competitions download` + geff parsing.
