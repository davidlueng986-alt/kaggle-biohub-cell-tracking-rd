# Plan — EXP-0007 DoG detection probe

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic (fixed percentile).
- Probe: `44b6_0113de3b` t∈{0,1,2} + `6bba_05b6850b` t∈{0,1,2} (real zarr,
  CPU). Detector: `scripts/dog_detect.py` (DoG + percentile + components).
- Operating points: pct ∈ {99.0 (primary), 99.5 (contrast)}.
- GT subgraphs: EXP-0003 GT JSON filtered to probe frames; T_true scaled
  ×3/100 (labeled approximate) + raw edge jaccard recorded (unpenalized
  view unaffected by the scaling).
- Links: `baseline_link.link` on detected nodes (causal, 7 µm).

## Cold-run steps

1. `bash experiments/EXP-0007/run.sh` — detect → match (P/R) → link →
   score → `metrics.json` + timing.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~minutes (6 frames × ~1 s detection + scoring). Full-video
  timing extrapolated, not run (H-005 note only).
