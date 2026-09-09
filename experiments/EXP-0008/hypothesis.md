# EXP-0008 — Full-frame DoG sweep + threshold curve (H-002 + H-005)

## Hypothesis

The EXP-0007 operating point (pct 99.0, recall 1.00) generalises beyond
probe frames to full videos: full-video recall ≥ 0.90 on both samples at
pct 99.0, with a monotone threshold curve on the t0–9 window
(recall 98.5 ≥ 99.0 > 99.5, counts/frame falling with pct). Full-video
image-based tracks linked by the frozen Hungarian linker will score below
the oracle floor (extra-track FP/FN pressure) with division 0 — the first
full-video image-based number, and the honest gap to close. Timing:
mean ≤ 2.5 s/frame expected (≈250 s/video detection alone — over the
80–96 s/video envelope, quantifying the H-005 optimisation debt, not
paying it here).

## Falsification criteria (as run)

- REJECT operating-point generality if full-video recall < 0.90 at pct 99.0
  on either sample (then threshold must adapt per-frame/intensity → new
  hypothesis; fixed percentile dead).
- Ceiling keep-trying (single deterministic run; promotion needs fold0 win
  + replication). No gate impact either way at this rung.

## Outcome (recorded 2026-09-09 — falsified as written, refined)

Full-video recall @99.0: 44b6 **1.000** but 6bba **0.835** → operating-point
generality REJECTED per the criteria above. Diagnosis: misses are a
consistent ~1 dimmer annotated cell/frame across 70 frames (not dim-frame
clusters), and the threshold is ALREADY per-frame (percentile of each
frame's own DoG) — so the prescribed "adaptivity" fix is wrong; the data
calls for a LOWER level: curve t0–9 shows pct 98.5 → recall 1.00 both
samples with monotone curve intact. Fixed percentile is NOT dead;
pct 99.0 is. EXP-0009: full-video @98.5 + count/edge tradeoff.

- REJECT operating-point generality if full-video recall < 0.90 at pct 99.0
  on either sample (then threshold must adapt per-frame/intensity → new
  hypothesis; fixed percentile dead).
- Ceiling keep-trying (single deterministic run; promotion needs fold0 win
  + replication). No gate impact either way at this rung.
