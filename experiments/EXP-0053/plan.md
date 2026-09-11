# Plan — EXP-0053 Trusted rebaseline

## Config / seeds

- Protocol v1.2 frozen. Scorer v1.1.0. Deterministic (no randomness anywhere:
  sorted grid/iteration, fixed tie-break in harness).
- Harness: `scripts/trusted_cv.py --full` (grid pct {96,97,98,98.5,99,99.5} ×
  gate {7,10}; fit = argmax micro on fit samples; tie-break micro desc,
  fewer detections, smaller gate, higher pct). Detection cache
  `experiments/EXP-0053/det/` (frozen artifacts reused by manifest, gaps
  detected on demand). Smoke gate passed: `--smoke` 2-sample run green in
  ~35 s (`/tmp/trusted_smoke.json`; nested HPs differ per holdout as designed).
- Output: `metrics.json` = harness envelope + `{exp_id, title,
  hypothesis_id, decision}`.

## Cold-run steps

1. `bash experiments/EXP-0053/run.sh` (full 6-sample LOSO + nested; long —
   detection gaps dominate, ~1–2 h; safe to nohup).
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only. Detection ~25 missing combos × 100 frames is the long pole;
  linking 96 (sample,config) runs cached and reused across folds.
