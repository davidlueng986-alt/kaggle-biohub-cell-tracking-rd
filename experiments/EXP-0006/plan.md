# Plan — EXP-0006 Replication rung

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Frozen challenger: fork r10
  (`scripts/fork_link.py --propose-um 10.0`), GT graphs from EXP-0003.
- Perturbation seeds {0,1,2}: `scripts/perturb_graph.py` (σ=0.3 vox) applied
  to pred-side node positions; scored vs clean GT (7 µm gate absorbs jitter
  for identity; proposal boundaries can flicker — that is the test).
- LOO: arithmetic on EXP-0005 r10 rows (drop each 6bba sample in turn;
  44b6 side has zero variance by construction — proposals never fire there).

## Cold-run steps

1. `bash experiments/EXP-0006/run.sh` — jitter → link → score per seed,
   LOO micros, verdict → `metrics.json`.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, minutes (3 seeds × 6 samples link+score).
