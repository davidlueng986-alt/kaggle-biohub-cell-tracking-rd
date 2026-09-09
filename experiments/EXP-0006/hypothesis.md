# EXP-0006 — Replication rung for r10 (H-002 + H-003)

## Hypothesis

The EXP-0005 r10 challenger (div 3/0/1, FP=0, fold1 +0.0011) is a stable
property of the geometry, not a knife-edge of exact voxel coordinates:
under seeded sub-voxel jitter (σ=0.3 vox ≈ 0.5/0.12 µm, ≪ 7 µm gate) the
same 3 GT divisions are recovered with FP=0 across seeds {0,1,2}, and
leave-one-sample-out worst-fold never drops below floor. Predicts:
per-seed div sums 3/0/1, edge within ±0.002 of unperturbed r10, LOO micros
all ≥ floor. Promotion still needs a fold0 win (§4 gate 1) — impossible
here (44b6 ties floor: 0 GT divs) — so the ceiling is `keep-trying` with
r10 upgraded from ensemble-candidate to **replicated challenger** on a
full pass; any flicker is recorded as a robustness limit, not hidden.

## Falsification criteria

- REJECT r10's stability claim if any seed adds an edge FP, loses a div TP
  that unperturbed r10 holds, or moves any sample edge by >0.002; or if any
  LOO micro drops below floor (then r10's gain hinges on one sample).
