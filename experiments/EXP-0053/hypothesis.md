# EXP-0053 — Trusted CV rebaseline, standing DoG stack (H-002/H-004, PROTOCOL v1.2)

## Hypothesis

Under nested HPs (fit on non-held-out samples only), the standing DoG+link
stack scores strictly below its tuned_ref numbers (0.8194-class), because
historical levels were locked on scored samples (selection leakage,
PROTOCOL v1.2 §2.1). The smoke preview already shows the mechanism:
holdout-6bba fitted on 44b6 picks pct 99.0 and scores 0.7121, not the
tuned 0.8194@98.5. Predicts: `loso_worst` well below 0.8194 (dark-sample
holdouts fitted on mismatched regimes), per-left-out HPs vary by holdout
(no universal level — consistent with EXP-0021/0034/0040 transfer
failures), and `embryo_nested_worst` below both embryo tuned micros.
This rung DEFINES the trusted standing (BTE); it does not promote
(single deterministic pass, baseline by construction).

## Falsification criteria

- If `loso_worst` comes out AT or ABOVE 0.8194, the selection-leakage
  diagnosis is wrong (levels transfer after all) — rewrite the v1.2 §2.1
  narrative and re-examine EXP-0021.
- Ceiling keep-trying (rebaseline defines standing; promotion needs a
  challenger that beats it under the same envelope).
