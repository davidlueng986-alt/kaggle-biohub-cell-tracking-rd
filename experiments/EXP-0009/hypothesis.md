# EXP-0009 — Full-video @98.5 + count/edge tradeoff (H-002)

## Hypothesis

Dropping the DoG threshold one notch (99.0 → 98.5) recovers the systematic
~1 dimmer annotated cell/frame missed in EXP-0008: full-video recall ≥ 0.95
both samples (curve t0–9: 1.00 both). Price: ~2× detections/frame, pushing
6bba toward/over its T_true=6362 (~45→~90/frame ≈ 4.5k–9k/video) — the
adjusted edge may fall even as raw edge rises (bonus→penalty crossover).
Predicts: recall recovery dominates (net score up both samples), 44b6 stays
near-perfect (sparse graph, T far above counts), division still 0 on these
two 0-division samples. Counts as operating-point selection, not promotion
(single deterministic run ceiling → keep-trying).

## Falsification criteria

- REJECT @98.5 if full-video recall < 0.95 either sample (then the dim-cell
  population needs more than a level shift → size/scale or appearance terms).
- REJECT the tradeoff if adjusted edge falls below the @99.0 level on either
  sample (then extra counts cost more than recall buys → threshold stays 99.0
  for sparse tissue / needs per-sample levels).
