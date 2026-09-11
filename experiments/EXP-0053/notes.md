# Notes — EXP-0053 Trusted rebaseline (H-002/H-004, v1.2)

## Log
- 2026-09-11: scaffolded; harness `scripts/trusted_cv.py` written; `--smoke`
  gate passed (2 samples, nested HPs differ per holdout as designed, 35 s).
- Full run launched (background): 6-sample LOSO + embryo-nested, grid
  pct{96,97,98,98.5,99,99.5}×gate{7,10}, det cache `experiments/EXP-0053/det/`.
- (fill on completion: loso_micro / loso_worst / embryo_nested_worst vs
  tuned_ref 0.8194 vs public 0.650/0.668; per-left-out HP table.)

## Decisions
- keep-trying (rebaseline defines standing; promotion needs a challenger
  under the same envelope).
