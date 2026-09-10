# EXP-0012 — Peak-splitter for dense frames (H-002)

## Hypothesis

Oversize DoG components in dense tissue are merged cells, splittable by
local-maximum peaks + Voronoi assignment (`scripts/dog_detect.py`
`--split-size 3000`, footprint (5,15,15), small parts merged losslessly).
Proven mechanism chain: (a) t25 probe — misses are DIM cells (DoG 49.7 vs
thr 60), matched cells sit in 1200–3500 vox components; (b) 2×2 window
t20–29 — splitter neutral at recall 1.00 (+7–11 det/frame, no harm);
(c) miss-heavy frames {10,42,43,44,55,66,77,88} — @98.5: 0.889 vs
@98.0+split: **0.986** at det/f 48→64. Lower threshold catches dim cells,
splitter repairs the merges it causes. Predicts full-video 6bba@98.0+split:
recall ≥ 0.95 with adj above @98.5's 0.8194; T_ratio ≈ 1.0 (parity watch —
penalty may just engage). Ceiling keep-trying (single deterministic run).

## Falsification criteria

- REJECT splitter value if full-video recall < 0.95 or adj < 0.8194 (then
  window gains do not transfer → splitter overfits window density).
