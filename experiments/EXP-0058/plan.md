# Plan — EXP-0058 Threshold-hysteresis union probe on 05db0fb1

## Config / seeds

- Sample: 6bba_05db0fb1, window t20–29 (10 frames, GT-dense).
- Detector: frozen `scripts/dog_detect.py` CLI, base sigmas, min-size 50,
  percentile mode. Two thresholds fixed a priori: @99.0 (anchors),
  @95.0 (halo). Fusion: drop @95.0 detections within 3 µm of any @99.0
  detection; union = anchors + surviving halo. Deterministic, no seeds.
- Matcher: `scripts/score.py:match_nodes`, voxel
  z=1.625/y=x=0.40625 µm, max 7.0 µm (PROTOCOL v1.2).
- Budget: exactly 20 CLI detections (10 frames × 2 thresholds).

## Steps

1. `bash experiments/EXP-0058/run.sh`:
   - Stage 1: CLI detect t20–29 @99.0 → `hi99_t<t>.json`,
     @95.0 → `lo95_t<t>.json` (20 files).
   - Stage 2: embedded python — pool per-frame nodes per config,
     `match_nodes` vs GT window (`experiments/EXP-0003/gt/`), NMS-fuse
     (3 µm gate), match union, write `metrics.json` + verdict.
2. Inspect `metrics.json`; record verdict in `notes.md`.

## Budget

CPU-only, deterministic, < 20 min (expected ~2–5 min; @95.0 on dense
tissue ≈ 4 s/frame per EXP-0024).
