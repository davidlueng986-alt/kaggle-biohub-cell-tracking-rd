# EXP-0027 — Detection-internals profile

## Hypothesis
Gaussian filters dominate detect() cost, with connected-component labeling second.

## Background
- Detection is ~99.5% of pipeline cost; linking is negligible (EXP-0025: 0.2-0.5%).
- Half-res detect failed quality full-video (EXP-0023 STOP); H-005 envelope is 80-96 s/video.
- Target: scripts/dog_detect.py detect() = float32 cast + 2x gaussian_filter + percentile + label + bincount + per-component argwhere/mean (split off).

## Falsification criteria
REJECTED by measurement: per-component argwhere loop (moments/means), not the
gaussians, dominates — 58.1% (dense 6bba, 0.47/0.81 s/f) and 84.8%
(sparse-ish 44b6, 1.85/2.18 s/f). Gaussians total only 32.5% / 11.6%; label
2.3% / 0.9% (a distant 4th/5th, not second). See metrics.json + notes.md.
