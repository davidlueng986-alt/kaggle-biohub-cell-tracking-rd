# Plan — EXP-0020 Combo replication

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Frozen challenger: `fork_link.link
  (propose_um=10.0, base_maxd=10.0)`. Noise-matched base: `BL.link
  (maxd=10.0)` on identical jittered inputs.
- Perturbation: `scripts/perturb_graph.py` σ=0.3 vox, seeds {0,1,2}, all 6
  GT graphs; scored vs clean GT (EXP-0006/0018 protocol).
- Bars recomputed from frozen artifacts inside run.sh (EXP-0019 rule).

## Cold-run steps

1. `bash experiments/EXP-0020/run.sh` → `metrics.json` + promote/keep verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~10 min (3 seeds × 6 samples × 2 arms link+score).
