# Plan — EXP-0008 Full-frame sweep + curve

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Samples: `44b6_0113de3b` + `6bba_05b6850b` (EXP-0007 probe pair, both
  embryos). Detector `scripts/dog_detect.py` (frozen DoG params).
- Curve: pct ∈ {98.5, 99.0, 99.5} × t0–9 window → recall/counts/time.
- Full video: pct 99.0 × all 100 frames → link (`baseline_link`, scipy fast
  path for N>60, pure below — oracle floor bit-identical) → score vs full
  GT with true T_true.
- Linker assigns backend recorded (`assign` field) for audit.

## Cold-run steps

1. `bash experiments/EXP-0008/run.sh` → `metrics.json` + timing table.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~10 min (260 frame-detections ≈ 6–8 min + linking/scoring).
  No GPU, no full-dataset download (2 subset samples only).
