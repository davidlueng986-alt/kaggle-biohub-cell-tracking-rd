# EXP-0028 — Vectorized centroids (H-005)

## Hypothesis

Replacing the per-component `argwhere` loop with a single
`center_of_mass` pass (uniform weights — identical math) yields
bit-identical detections at lower cost: node POSITION sets equal on every
validation frame (6/6 probe frames already identical, 0 mismatches), and
the linked window edge equals EXP-0013 A exactly (143/2/5). Measured
speedup ~1.3× dense (0.85→0.64 s/f) to ~3× sparse (2.05→0.67 s/f on t25;
EXP-0027's 43%/79% projections were optimistic — gaussian/label share
grows as moments shrink, honestly recorded). Gate: fidelity identical on
ALL window frames (t20–29 + t40–49 6bba, t20–29 44b6 control) AND linked
edge == A → ADOPT unconditionally (strictly-better-or-equal code, zero
quality change); timing gain is a measurement, not a gate (any speedup
≥1.2× still banked). Ceiling keep-trying (infra rung; no metric movement
by design — a metric move would be a fidelity FAILURE).

## Falsification criteria

- REJECT (revert to loop) on ANY frame with differing node sets or window
  edge ≠ 143/2/5 (fidelity breach — speed never trades correctness).
