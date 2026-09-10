# EXP-0026 — ROI-masked DoG acceleration

## Hypothesis

Detection is ~99.5% of pipeline cost (EXP-0025: linking 0.2–0.5%) and the
paydown target under H-005 (80–96 s/video envelope). A cheap foreground
mask (strided half-res intensity, O(1M) voxels + labeling) isolates bright
cell regions; running the FROZEN full-res DoG (`dog_detect.detect`,
unmodified) only inside per-component boxes with halo context cuts
processed voxels to ~50% (q=98) while preserving full-frame detections.
Predicts on the density-spanning window (t20–29 + t40–49, GT-dense):
ROI recall within 0.01 AND linked-block raw edge within 0.005 of fresh
full-frame @98.5 with wall speedup ≥ 2× → GO to full-video (EXP-0028).

## Background

- Protocol v1.1 frozen; scorer v1.1.0; deterministic CPU-only.
- Detector `scripts/dog_detect.py` (~0.8–2 s/frame full-frame).
- EXP-0023: half-res detect FAILED full-video quality (speedup real,
  parity the blocker — same shape expected here if per-box thresholds
  diverge from the global one).
- EXP-0024: fixed thresholds dead on dark samples → mask threshold is an
  adaptive half-res percentile, NOT an absolute intensity.
- EXP-0013 reference window: base @98.5 recomputed fresh here (never
  pasted; brief cites rec 0.982, raw 0.9533, ec 143/2/5).

## Falsification criteria

- REJECT ROI masking if on the window EITHER readout misses parity
  (ROI recall < FULL − 0.01 OR ROI raw < FULL − 0.005) OR speedup < 2×.
  Either failure → STOP with measured bottleneck breakdown (mask vs
  DoG-vs-label shares); no full-video commit (EXP-0028 stays a
  recommendation only).
