# Notes — EXP-0008 Full-frame sweep + curve (H-002+H-005)

## Log
- 2026-09-09: `bash experiments/EXP-0008/run.sh` → exit 0, metrics recorded
  with falsified check (ledger keeps falsified runs; `run.sh` dumps before assert).
- Threshold curve t0–9 (recall): 44b6 {98.5: 1.00, 99.0: 1.00, 99.5: 0.00};
  6bba {98.5: 1.00, 99.0: 1.00, 99.5: 0.576}. Monotone ✓.
- Full-video @99.0: 44b6 recall **1.000**, edge_raw 0.9038 / adj 0.9382
  (47/2/3 — first STRONG full-video image-based number); 6bba recall
  **0.835**, edge_raw 0.6922 / adj 0.7121 (623/55/222). Division 0/1.0-empty
  both (no GT divisions in these two samples — 05b6850b/0113de3b are the
  0-division ones).
- Falsified generality → diagnosed (70 frames each missing ~1 dimmer
  annotated cell; threshold already per-frame) → refined to LEVEL fix:
  EXP-0009 full-video @98.5.
- Infra: `baseline_link` gained a scipy C fast path (N>60, same optimum,
  deterministic); oracle floor re-verified bit-identical (pure path).
  6bba full-video linked pure (N~45/frame); 44b6 via scipy (N~160/frame).
- Timing (H-005): detect mean 2.05 s/frame (44b6, 205 s/video) and
  0.84 s/frame (6bba, 84 s/video) — detection alone meets-or-busts the
  80–96 s/video envelope. Optimisation debt: downsample/ROI/mask pre-pass,
  sigma tuning, component-size short-circuit. No submit-path use until paid.

## Decisions
- `keep-trying` — falsified operating point, refined direction. pct 99.0
  dead for 6bba-grade density; @98.5 test next (EXP-0009) with count/edge
  tradeoff watch (more detections → T_true pressure: 6bba T=6362 vs
  ~45→~90 det/frame ≈ 4500–9000/video — may cross from bonus into penalty).
