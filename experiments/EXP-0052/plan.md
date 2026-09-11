# Plan — EXP-0052 H-005 hidden timing calibration from v7 logs + local det artifacts

## Config / seeds
Deterministic, stdlib-only, CPU-only. No seeds (closed-form least squares).
Basis: 199 hidden videos x 100 frames = 19900 frames vs 12 h cap.

## Steps
1. `bash experiments/EXP-0052/run.sh`: fetches v7 log via
   `kaggle kernels logs liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10`
   (read-only; full 31-record log, no `-f` needed) into `v7_visible.log`,
   then runs `calibrate.py` (parse 4 per-video lines, fit local + Kaggle
   models, project 3 regimes + 2x-dense robustness) into `metrics.json`.
2. Verify: visible total 437 s = 0.1214 h matches kernel "total 0.12h" line.
3. Read verdict/headrooms from `metrics.json` for RESULTS/STATE.

## Budget
< 25 min wall-clock; analysis-only (no kernel runs, no pushes/uploads).
