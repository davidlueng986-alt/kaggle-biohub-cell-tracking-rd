# Plan — EXP-0029 Truncate gate + kernel v6

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Window t20–29 + t40–49 6bba @98.5: A = frozen EXP-0013 A_t files vs T2 =
  fresh `--truncate 2.0` detects. Position equality + linked edge + timing.
- Kernel: port vectorized centroids + truncate into
  `notebooks/submit_gold/submit_gold.ipynb` detect_frame (only if T2 gate
  passes; centroids regardless — already adopted in EXP-0028), push
  (no leaderboard submit), visible COMPLETE + timing comparison.

## Cold-run steps

1. `bash experiments/EXP-0029/run.sh` → truncate verdict in metrics.json.
2. Notebook edit + `kaggle kernels push` + monitor to COMPLETE.
3. `bash scripts/run_loop.sh --dry-run`.
4. Knowledge + commit + push.

## Budget

- CPU-only. Window detects ~10 min; kernel visible run ~20 min + queue.
