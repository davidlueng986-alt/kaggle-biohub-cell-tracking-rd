# EXP-0015 — Appearance-similarity probe (H-003)

## Hypothesis

Leftover-confusion FPs (the documented link failure across EXP-0012–0014)
are geometrically plausible but photometrically wrong: patch NCC between
link endpoints separates scored-TP from scored-FP edges on the frozen
6bba@98.5 full-video graph (699 TP / 30 FP — FP-rich enough to measure;
44b6's 2 FPs cannot power this test). Predicts: mean NCC(TP) exceeds mean
NCC(FP) by ≥ 0.15 with modest overlap (FP 75th pct < TP 25th pct) — a
signal an appearance-weighted assignment (EXP-0016) can spend. This is a
MEASUREMENT rung: no linker changes, no thresholds spent. Ceiling
keep-trying regardless.

## Falsification criteria

- REJECT classical appearance if the margin < 0.15 or overlap is gross
  (then patch NCC at cell scale is uninformative → park H-003 classical;
  dim/confusion links need learned features — GPU-notebook territory).
