# EXP-0011 — Full-video 6bba@98.0 (H-002)

## Hypothesis

The @98.0 window signal (recall 1.00, det/f 57) carries to full video:
6bba full-video recall ≥ 0.95 at pct 98.0 with adjusted edge above the
@98.5 level (0.8194) — the dim tail converts to TPs faster than the +21%
counts cost bonus. 44b6 stays locked @99.0 (recall 1.000 there; untouched
this rung). T_ratio watch: ~5.7k detections vs T_true=6362 (≈0.90) —
approaching parity from below; no penalty expected yet, crossover flagged
if T_ratio ≥ 1.0. Predicts monotone descent payoff: 98.5→98.0 improves both
recall and adj on 6bba. Ceiling keep-trying (single deterministic run).

## Falsification criteria

- REJECT @98.0 if recall < 0.95 (window signal did not carry → descent
  stops; dim tail needs size/appearance terms, not level).
- REJECT the level if adj falls below @98.5's 0.8194 (counts cost more
  than tail buys → level stays 98.5 for 6bba).
