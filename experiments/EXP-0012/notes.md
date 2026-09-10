# Notes — EXP-0012 Splitter full-video (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0012/run.sh` → exit 0, split verdict.
- 6bba@98.0+split3000: recall **0.993** ✓ (0.893 → 0.993: dim tail AND
  merges fixed, 595 splits) but adj **0.7088** ✗ (< 0.8194): ec 717/168/128
  vs @98.5's 699/30/146 — TP +18, FN −18, but FP 30→**168**. T_ratio 0.99
  (parity reached; penalty factor ≈1.0 — damage is edge-FP, NOT T penalty).
- Mechanism: split fragments link aggressively — extras near GT tracks hit
  the sparse-rule FP cases (target/source matched to annotated nodes with
  other partners). Suspected over-splitting too (elongated single cells
  clearing the (5,15,15) footprint twice → duplicate detections, one matches,
  one pollutes). Timing 0.93 s/f (splitter cheap — H-005 neutral).
- Diagnosis chain preserved: t25 dim-vs-merge probe → 2×2 window →
  miss-frame recovery (0.889→0.986) → full-video. The window recovery was
  REAL (recall transferred); the FP price only appears at full-video link
  scale. Lesson: window gates must include a linking/FP readout, not recall
  alone.

## Decisions
- `keep-trying` — splitter value falsified AS-IS (adj −0.111). Standing
  policy stays 44b6@99.0 + 6bba@98.5 (worst 0.8194). Refinement, not
  abandonment: split parts are real cells 99% of the time (recall proves
  it) — the linker must treat them conservatively.
- Next EXP-0013: prominence-gated splits (secondary peak ≥0.7× primary or
  no split) + conservative linking of split parts, window-first WITH edge
  readout (link the window frames and score the subgraph — no more
  recall-only gates).
