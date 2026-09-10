# Plan — EXP-0024 Per-sample threshold map

## Config / seeds
- Deterministic: fixed pct grid {97.5, 98.0, 98.5, 99.0, 99.5}, frozen DoG
  sigmas (1,3,3)/(1.6,5,5), min-size 50, thr_mode=percentile. No randomness,
  no seeds. CPU-only.
- Data: data/train/<sid>.zarr (gitignored, read in place — never copied).
- GT: experiments/EXP-0003/gt/<sid>_gt.json. Window t=20..29 (10 frames).
- Scope: detection/recall-only. No edges, no linker, no score.py full metric.

## Steps
1. Cold reproduce: `bash experiments/EXP-0024/run.sh` from repo root.
   run.sh calls `experiments/EXP-0024/sweep.py`, which for each of
   3 samples x 5 pcts x 10 frames runs `scripts/dog_detect.detect`
   (same code path as the `dog_detect.py` CLI defaults), matches window
   detections vs GT via `scripts/score.match_nodes`, and writes
   `experiments/EXP-0024/metrics.json` with the per-sample x pct table,
   best-pct selection, and verdict.
2. Check metrics.json verdict: TRANSFER-RESCUED (all >= 0.90) else
   NOT-RESCUED + dark-sample list.
3. No scorer invocation (no pred graphs built on this rung by design).

## Budget
~7-8 min wall on CPU (150 detections, 1-4 s/frame by density). Cap 25 min.
