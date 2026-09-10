# Plan — EXP-0039 05db0fb1 full-video @96.0 recall-vs-count-cost test

## Config / seeds

- Sample: 6bba_05db0fb1, all 100 frames (t=0..99), CPU-only, deterministic.
- Detector: `python3 scripts/dog_detect.py data/train/6bba_05db0fb1.zarr
  --t <T> --pct 96.0 --out experiments/EXP-0039/full_6bba_05db0fb1_t<T>.json`
  (all other flags default; deterministic; vectorized centroids).
- Linker: `baseline_link.BL.link({"nodes": nodes, "edges": []})` with
  defaults (gate 7 um — image-side gate policy; do NOT widen). Detection
  files restart ids per frame, so reassign GLOBALLY unique ids per video
  before linking.
- Scorer: trusted scripts/score.py v1.1.0 vs full GT with true T_true=69800.
  Runtime-only scipy assignment solver (see notes.md); scripts/* unmodified.
- Baseline: EXP-0021 `6bba_05db0fb1_pred.json` (@98.5) re-scored fresh.

## Steps

1. Run `./experiments/EXP-0039/run.sh` cold (detect → link → score →
   metrics.json). Exits 0; verdict recorded in metrics.json either way.
2. Check `metrics.json` comparison table + verdict (GO/MIXED/FAIL rule in
   hypothesis.md).
3. Spot-check `scores.json` for raw scorer outputs of both arms.

## Budget

CPU-only, < 35 min total: detect ~100×0.68 s ≈ 2–3 min, link ~5 min,
score ~1 min (scipy-backed exact assignment, equivalence-gated).
