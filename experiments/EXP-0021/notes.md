# Notes — EXP-0021 Image-policy transfer (H-002)

## Log
- 2026-09-09/10: `bash experiments/EXP-0021/run.sh` → exit 0, transfer
  REJECTED 3/6 (metrics recorded). Reused frozen EXP-0008/0009 detections
  for reference samples after a position-equality spot gate (dict schema
  evolved with split/parent keys since — timings excluded as noise).
- Per-sample @ per-embryo levels (44b6@99.0 / 6bba@98.5):
  - 44b6_0113de3b: rec 1.000, adj 0.9382 (reference holds).
  - 44b6_0b24845f: rec 0.325, adj 0.1040 — REJECT.
  - 44b6_0c582fdc: rec 0.197, adj 0.0958 — REJECT.
  - 6bba_05b6850b: rec 0.893, adj 0.8194 (reference holds).
  - 6bba_05db0fb1: rec 0.290, adj 0.2092 (dense: 262 det/f) — REJECT.
  - 6bba_062c8d37: rec 0.930, adj 0.8647 (transfers; beats 05b6850b).
- Embryo micros: 44b6 0.341 / 6bba 0.579 / worst 0.341. Division: image
  one-to-one links → div 0 everywhere GT divs exist (05db0fb1 FN 3,
  062c8d37 FN 1) — standing H-003 image gap.
- Diagnosis: levels key on embryo MEAN intensity, but samples vary more
  within embryo than embryos differ — 05db0fb1 is dense AND dim (262
  det/f yet recall 0.29: most detections are bright clutter, annotated
  cells dimmer than the cutoff). Fixed percentiles cannot transfer;
  per-sample/intensity-aware calibration required (measure-then-set:
  e.g. target recall proxy from DoG response distribution shape, or match
  detection density to T_true-implied density per video).
- Timing: 0.85–3.12 s/frame by density (05db0fb1 densest) — H-005 profile
  extended: cost scales with detections, not just frames.

## Decisions
- `keep-trying` — transfer REJECTED as stated; per-embryo fixed levels
  demoted from policy to starting points. Fallback @98.5 for unseen
  embryos is SUSPECT (recorded submit risk 2026-09-10).
- Next: EXP-0022 intensity-aware level calibration (per-video self-set
  threshold from DoG statistics + T density prior, window-gated) AND/OR
  H-005 timing paydown (downsample/ROI). Close submit loop first.
