# EXP-0005 — Tighter fork gating: radius ablation (H-002 + H-003)

## Hypothesis

The EXP-0004 radius-15 noise (10 FPs) comes from over-wide proposals, not
from forking per se: GT daughter separations measured 8.5–12.5 µm, so a
radius just above ~9 µm should recover divisions with ~zero FPs. Predicts a
plateau: r∈{10,11} recovers all in-reach divisions (3/4; the 12.49 µm pair
needs r≥13) with FP=0, r=9 under-recovers, r≥12 degrades. Radius never
exceeds EXP-0004's 15 (constraint). Isolation (nearest-source crowd veto)
is ablated as a second gate; expected no-op at tight radii. Matching gate
stays 7 µm. Verdict via sub-gate + fold micros vs EXP-0003 floor; promotion
additionally needs a fold0 (44b6) win per §4 gate 1 — none is expected
(44b6 has zero GT divisions), so the ceiling here is challenger/
ensemble-candidate status, decided honestly below.

## Falsification criteria

- REJECT tighter-gating if no radius shows division gain with zero FPs
  (then geometry alone cannot separate mitoses → H-003 appearance required).
- Single deterministic run → `keep-trying` ceiling regardless; promotion
  needs EXP-0006 replication rung.
