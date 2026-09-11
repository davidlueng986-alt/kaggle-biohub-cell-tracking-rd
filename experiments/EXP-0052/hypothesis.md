# EXP-0052 — H-005 hidden timing calibration from v7 logs + local det artifacts

## Hypothesis
Per-frame detection cost is linear in detections/frame with a dominant
fixed intercept, so hidden-test total time is bounded well below the 12 h
cap for any plausible density mix (199 videos x 100 frames).

## Background
- v7 gate-7 kernel COMPLETE on visible (4 videos, 0.12 h); hidden rerun
  COMPLETE-scored (ref 56153940, publicScore 0.668). Hidden per-video cost
  distribution unknown; prior local projection ~5.5 h assumed visible-like mix.
- Local evidence: 1000 frozen per-frame det records (EXP-0008 200,
  EXP-0009 200, EXP-0021 600) with params.elapsed_s; Kaggle anchor: 4 v7
  per-video totals from the fetched kernel log.

## Falsification criteria
- Reject linearity if local fit R2 < 0.9 (observed 0.995 vs kept dets).
- Reject "fits" verdict if any projection (sparse/mix/dense, incl. 2x-dense
  robustness) exceeds 12 h (observed max 6.92 h, headroom >= 1.73x).
- Note correction to prior assumption: 44b6 is mid-density (128-169
  det/frame), not sparsest; 6bba spans both extremes (47 / 262 det/frame).
