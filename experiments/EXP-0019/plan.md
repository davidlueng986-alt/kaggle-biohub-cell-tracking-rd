# Plan — EXP-0019 Gate-10 + r10 combo

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- All 6 oracle GT graphs: `fork_link.link(gt, propose_um=10.0,
  base_maxd=10.0)` (r10 rule on gate-10 base; isolation off per EXP-0005
  plateau finding). Default path verified bit-identical to frozen r10.
- Bar: NEW best (EXP-0018: 44b6 1.0998 / 6bba 1.0884, div 0/0/4).
  Need: div TP ≥ 1 (FP ≤ 1) AND edge ≥ best both folds.

## Cold-run steps

1. `bash experiments/EXP-0019/run.sh` → `metrics.json` + verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, minutes (graph ops on 6 GT graphs).
