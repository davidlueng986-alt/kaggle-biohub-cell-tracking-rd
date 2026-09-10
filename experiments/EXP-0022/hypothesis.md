# EXP-0022 — Self-calibration + timing paydown (H-002/H-005)

## Hypothesis

Two coupled claims: (a) a MAD rule (median+k·MAD) self-calibrates per
video where percentiles follow tail mass — falsified ON FIRST CONTACT
(t25: thr 3.8–7.8 vs pct-thr 60, FEWER detections 24–32 vs 45, recall
5–6/8 vs 8/8 — background-noise MAD sits at background, merging everything;
recorded, parked); (b) half-res y/x detection maps back with recall parity
at ~4–5× speed (t25: 0.20 s vs 0.81–0.96 s, recall 8/8, n=34 vs 45).
Predicts on the gate window (t20–29 + t40–49): DS (@98.5 downsample)
recall within 0.01 of A (@98.5 full-res, expected = EXP-0013 A numbers:
rec 0.982, raw 0.9533 — determinism anchor, asserted), raw within 0.005,
at ≥2.5× speedup. Gate: all three → full-video GO (EXP-0023) + kernel
upgrade path (H-005 paydown); else stop. Ceiling keep-trying (window rung).

## Falsification criteria

- REJECT downsample parity if recall gap > 0.01 or raw gap > 0.005
  (then half-res loses cells that matter → full-res cost stands, H-005
  needs ROI/mask ideas instead).
- MAD-pure already falsified at probe scale (above); no window matrix spent.
