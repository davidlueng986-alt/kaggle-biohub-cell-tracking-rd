# EXP-0047 — gate-10 vs gate-7 on dark image graphs

## Hypothesis
Gate-7 (v7 submit choice) holds on dark image graphs: gate-10 does not improve
adjusted edge Jaccard on dense/dark detections (cf EXP-0017 arm2: gate-10 harmful
−0.0060 on dense 6bba graph).

## Background
Probe proved gate-7 ≥ gate-10 on 4 visible samples; v7 (gate-7) PENDING hidden.
EXP-0021 dark graphs used gate-7 (default). Untested: gate-10 on dark.

## Falsification criteria
If gate-10 beats gate-7 (adj) on ≥3/5 dark+ref samples → CHALLENGE-g7 (revisit v7 interpretation).
Else HOLD-g7.
