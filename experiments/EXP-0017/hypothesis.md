# EXP-0017 — Link-gate ablation + gap-closing (H-002/H-005)

## Hypothesis

The 55 oracle FNs are 52 fast-motion adjacent pairs (7–10 µm) + 3
mismatches — diagnosed, not guessed — so the linking gate (a METHOD
hyperparameter; scorer gate stays 7 µm per PROTOCOL v1.1) is the mistuned
knob, not missing machinery: gate 10 recovers ~50 FNs at FP cost ~1 on
oracle graphs, and gate 14 adds only FPs (dominated). One-to-one pairing
keeps ≤1 outgoing edge per source at every gate → division-neutral by
construction (verified in verdict, not assumed). On the image-based
6bba@98.5 graph (real detection gaps), a conservative t→t+2 gap pass
(unmatched sources only → fork-free; gate 14 µm) recovers FNs at small FP
cost, and gate-10 base links stack with it. Predicts: arm1 gate10 embryo
micros ≥ floor both folds with div sums unchanged-or-better; arm2 best
config beats @98.5 base (adj 0.8194). Ceiling keep-trying (single
deterministic pass; a gate-10 result this strong becomes a promotion
CANDIDATE pending EXP-0018 jitter replication, same bar as r10).

## Falsification criteria

- REJECT wider gates if FP price exceeds FN recovery on either fold micro
  (then fast pairs are ambiguous, not merely gated).
- REJECT gap-closing if conservative pass adds net FPs without FN recovery
  on the image graph (then detection gaps are unbridgeable geometrically).
