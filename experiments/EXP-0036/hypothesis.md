# EXP-0036 — Notebook↔repo drift audit (submit path)

## Hypothesis

The submit notebook's inlined copies (detect/link/assign/CSV) behave
identically to repo scripts on frozen frames: detection position sets
EQUAL, linked edges EQUAL on 3-frame chains, CSV writer byte-equal on a
synthetic graph. Any delta is an enumerated, accepted parameter difference
(gate override, missing opts), not silent rot. Ceiling keep-trying
(audit rung; no metric movement possible).

## Falsification criteria

- DRIFTED on any behavioral inequality (positions, edges, writer bytes) —
  then patch the notebook before any further submit work.
