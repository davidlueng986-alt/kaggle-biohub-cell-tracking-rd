# Plan — EXP-0018 Gate-10 replication

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Frozen challenger: `BL.link(maxd=10)`.
- Perturbation: `scripts/perturb_graph.py` σ=0.3 vox, seeds {0,1,2}, all 6
  GT graphs; scored vs clean GT. Noise-matched base: same jittered graphs
  linked gate-7 (`maxd` default).
- LOO: same-subset head-to-head (gate-10 vs floor), EXP-0006-corrected
  method. Embryo micros + div sums throughout.

## Cold-run steps

1. `bash experiments/EXP-0018/run.sh` → `metrics.json` + promote/keep verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~10 min (3 seeds × 6 samples × 2 gates link+score).
