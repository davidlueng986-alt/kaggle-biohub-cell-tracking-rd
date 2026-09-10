# Plan — EXP-0037 Rescore reproducer

## Config / seeds

- Deterministic. Inputs: frozen `*_submit_pred.json` graphs (parsed from
  the v6 visible output CSV) + EXP-0003 GT + `*_ref_score.json` bars
  recomputed with gate-7 links.
- Run: `bash experiments/EXP-0037/run.sh` re-scores all four with
  `score.py` v1.1 and asserts the recorded table (parse + score
  reproducibility, not re-derivation of the CSV parse itself).

## Cold-run steps

1. `bash experiments/EXP-0037/run.sh` → `metrics.json`.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~2 min (4 scorings of frozen graphs).
