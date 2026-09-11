# Notes — EXP-0053 Trusted rebaseline (H-002/H-004, v1.2)

## Log
- 2026-09-11: scaffolded; harness `scripts/trusted_cv.py` written; `--smoke`
  gate passed (2 samples, nested HPs differ per holdout as designed, 35 s).
- Full run launched (background): 6-sample LOSO + embryo-nested, grid
  pct{96,97,98,98.5,99,99.5}×gate{7,10}, det cache `experiments/EXP-0053/det/`.
- COMPLETED 2026-09-11 (~68 min): loso_micro **0.4826**, loso_worst **0.2092**
  (holdout 05db0fb1, HP 98.5/7), embryo_nested fold0 0.4193 / fold1 0.6136 /
  worst **0.4193** (both folds fit HP 97.0/7.0). Per-left-out HPs vary
  (96–98.5, gate always 7 — gate-10 never selected under nesting).
  Selection-leakage diagnosis CONFIRMED (0.2092 << tuned_ref 0.8194).
  Falsification bar (worst ≥ 0.8194) not met — v1.2 §2.1 narrative stands.
  LB calibration: |0.4826 − 0.65| = 0.167 > 0.15 → FLAG `cv_lb_miscalibrated`
  recorded in `knowledge/LB_CALIBRATION.md` (subset harder per-sample than
  hidden; scale effects). Defines trusted standing (BTE).

## Decisions
- keep-trying (rebaseline defines standing; promotion needs a challenger
  under the same envelope).

## Completion (2026-09-11 gold-watch)
- loso_micro **0.4826**, loso_worst **0.2092** (holdout 6bba_05db0fb1 @98.5/gate7).
- embryo_nested: fold0(44b6) micro **0.4193** / fold1(6bba) **0.6136** / worst **0.4193** (both nested HPs @97.0/gate7).
- vs tuned_ref 0.8194: selection-leakage confirmed (hypothesis holds).
- vs public LB 0.650/0.668: public above trusted worst (diagnostic only).
- decision: keep-trying — BTE defined; next challenger under same trusted envelope.
