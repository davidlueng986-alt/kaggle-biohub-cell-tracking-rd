# EXP-0004 — Fork-proposing linker variant, division sub-gate test (H-002 + H-003)

## Hypothesis

Adding locally-evidenced forks (second daughter within a declared 15 µm
proposal radius, unmatched target only, ≤1 extra per source) to the EXP-0003
oracle Hungarian links recovers real GT divisions (3/4 sit 8.5–12.5 µm apart
— beyond the 7 µm matching gate, measured 2026-09-09) at an acceptable
edge-FP price. Predicts: division-TP gain on 6bba division samples, zero
change on 44b6 (no GT divisions there), small edge movement either way.
Verdict goes through the PROTOCOL v1.1 division sub-gate: fork-count
increase needs division gain AND no adjusted-edge regression on BOTH folds.
Proposal radius (15 µm) is a declared hyperparameter, ablated in EXP-0005+;
matching gate stays 7 µm. Geometry-only precursor to H-003 appearance
gating. See `docs/PROTOCOL.md` §§1/4–5.

## Falsification criteria

- REJECT for promotion if adjusted-edge regresses on either fold OR no
  division gain materialises (then the radius proposes noise, not mitoses).
- `promote` additionally needs ≥2-seed replication (§4 gate 1) — single
  deterministic run caps at `keep-trying` regardless of numbers.
