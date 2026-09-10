# EXP-0016 — Soft appearance-weighted assignment (H-003)

## Hypothesis

Folding patch NCC into assignment cost (cost = um_dist + W·(1−NCC),
geometry still the only gate) fixes leftover-confusion links without
buying TP damage: on the gate window (t20–29 + t40–49, @98.5 base
detections reused from EXP-0013 — no new detection), some W ∈ {1,2,4}
beats geometry-only (W=0) on window edge with TP-cost ≤ 1 flipped GT-TP
edge (explicit budget). W=0 must reproduce EXP-0013 A bit-exactly
(143/2/5 — anchor asserting the NCC path perturbs nothing by itself).
Gate: a W ≥ A(W=0) on recall+raw+adj → full-video GO (EXP-0017). Else stop.

## Falsification criteria (as run)

- REJECT soft weighting if no W beats W=0 on all three readouts, or if
  every winning W flips >1 GT-TP edge (TP-cost over budget).

## Outcome (recorded 2026-09-09 — null treatment, gate overruled)

W=1/2/4 byte-identical to W=0; W=8/16/32 also identical (penalties up to
64 µm flip nothing). GO-by-equality was mechanically True but overruled:
a provably inert treatment must not consume a full-video rung. H-003
classical PARKED (see notes for mechanism: shared-tissue patches).
