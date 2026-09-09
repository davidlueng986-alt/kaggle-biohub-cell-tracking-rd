# EXP-0007 — DoG detection probe on real zarr (H-002, CPU-only)

## Hypothesis

A classical DoG detector (σ=(1,3,3)/(1.6,5,5) vox, percentile threshold,
connected components, CPU ~1 s/frame) reaches GT recall ≈ 1.00 on probe
frames at pct=99.0 — because annotated cells are bright-but-not-brightest,
raising the threshold collapses recall (measured 2026-09-09: 99.0→1.00,
99.5→0.00–0.33, 99.9→0.00 on both probe samples). End-to-end mini-graphs
(detected nodes t0–t2 + Hungarian links, scored vs GT subgraphs) will score
well below the oracle floor (extra real-but-unannotated tracks create
FP/FN pressure under the sparse-aware rules) with division 0 (one-to-one
links). Predicts: pct 99.0 dominates 99.5 on recall and edge; per-frame
time ~1–2 s (H-005 budget watch: ×100 frames ≈ 60–180 s/video detection
alone — over the 80–96 s/video envelope without optimization).

## Falsification criteria

- REJECT DoG-viability if pct-99.0 recall < 1.00 on either probe sample
  (then even the operating point misses annotated cells → wrong scale or
  broken response).
- This is a PROBE (2 samples × 3 frames), not a model: ceiling keep-trying
  regardless. Promotion needs full-video detection + gates.
