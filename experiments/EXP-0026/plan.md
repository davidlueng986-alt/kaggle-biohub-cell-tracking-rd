# Plan — EXP-0026 ROI-masked DoG acceleration

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic (sorted boxes/nodes).
- Sample: `6bba_05b6850b` (dense). Window: t20–29 + t40–49 (20 frames).
- FULL: fresh `scripts/dog_detect.py @98.5` per frame (recompute, never paste).
- ROI primary: `experiments/EXP-0026/roi_detect.py` q=98, halo (6,16,16),
  pct=98.5, min_size=50. ROI secondary (Pareto point): q=95, same rest.
- `scripts/dog_detect.py` is NEVER edited; wrapper imports its `detect`.
- Readouts per config: window micro-recall, det count, linked-block edge
  (raw + adj) vs GT subgraph (T_true ×20/100), wall s/frame, speedup ratio.

## Steps

1. `bash experiments/EXP-0026/run.sh` → detection (FULL + ROI q98 + ROI q95),
   micro-profile (full-frame DoG-vs-label shares, ROI mask-vs-loop shares),
   link blocks + score + gate verdict → `metrics.json`.
2. Inspect `metrics.json`; GO → recommend EXP-0028 full-video (do NOT run
   it here); STOP → record bottleneck breakdown in `notes.md`.

## Budget

- CPU-only, ~5 min (60 frame-detections ≈ 20×0.85 + 20×0.25 + 20×0.5 s
  plus link/score overhead). Single window, well under the 25-min cap.
