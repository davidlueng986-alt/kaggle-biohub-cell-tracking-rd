# Notes — EXP-0009 Full-video @98.5 (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0009/run.sh` → exit 0, mixed verdict recorded.
- 44b6_0113de3b: recall 1.000 ✓ but adj 0.9281 < 0.9382 (@99) ✗ — raw
  IDENTICAL (47/2/3); extra detections (188 vs ~160/frame, T_ratio 0.73)
  bought zero links and cost bonus. Pure count penalty, no gain.
- 6bba_05b6850b: recall 0.835 → 0.893 (up, but <0.95 ✗); raw 0.6922 →
  0.7989, adj 0.7121 → **0.8194** ✓ (+76 TP, −25 FP, −76 FN → 699/30/146).
  Level helps a lot, yet dimmest cells still missed; T_ratio 0.74 (still
  bonus territory — penalty crossover NOT reached, watch continues).
- Link backends: 44b6 scipy (N~188/frame), 6bba pure (N~47/frame).

## Decisions
- `keep-trying` — falsified on both written counts, refined: @98.5 vs @99.0
  SPLITS by sample (6bba +0.107 adj, 44b6 −0.010 adj). Justified next step:
  **per-sample (per-embryo) operating levels** — 44b6 stays @99.0, 6bba goes
  @98.5 (combo = best-of-both, no new machinery). EXP-0010: formalize combo
  + probe 6bba@98.0 on window (cheap) for the remaining dim tail.
