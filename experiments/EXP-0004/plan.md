# Plan — EXP-0004 Fork-proposing linker variant

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic (no randomness).
- Subset 6 (same as EXP-0003). Base: `scripts/baseline_link.py` oracle
  Hungarian links. Variant: `scripts/fork_link.py --propose-um 15.0`
  (one extra edge per source max, unmatched targets only, causal t→t+1).
- Floor reference: `experiments/EXP-0003/metrics.json` (worst-fold 1.0705,
  div 0/0/4). Folds: fold0 = 44b6 holdout (n=3, stability — zero GT divs),
  fold1 = 6bba holdout (n=3, gain opportunity — 4 GT divs).

## Cold-run steps

1. `bash experiments/EXP-0004/run.sh` — links variant preds, scores all 6
   with `score.py` v1.1, compares vs EXP-0003 floor per sample + per embryo
   micro-average, evaluates sub-gate, writes `metrics.json`.
2. `bash scripts/run_loop.sh --dry-run`.
3. Both exit 0. Gate verdict recorded even when negative (no bare scores).

## Budget

- CPU-only, seconds–minutes (graph ops on GT JSON, no image reads).
