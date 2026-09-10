# Plan — EXP-0038 T-discipline track filter

## Config / seeds

- Deterministic, CPU-only; no randomness, no seeds needed. All iteration
  sorted (union-find with smaller-id root, sorted components, sorted
  rescue priority, sorted output nodes/edges).
- Filter params: `--min-len 6` (frames = distinct `t` per weakly-connected
  component), `--rescue-frac 0.05` (budget = floor(0.05 * kept nodes);
  rescue priority longest-first: `-frame_len, -node_count, min node id`;
  whole tracks only).
- Data: frozen preds above; GT with true T_true (scorer default; no
  `--T-true` override). No embryo split — direct before/after on 2 samples.

## Steps

1. Cold run: `./experiments/EXP-0038/run.sh` — filters both frozen graphs
   (`filter_tracks.py`), scores unfiltered + filtered per sample with
   `python3 scripts/score.py --pred <pred> --gt <gt> --out <json>`
   (true T_true), assembles `metrics.json` via `make_metrics.py`.
2. Read gate verdict from `metrics.json` (`gate.pass` / `gate.verdict`).
3. No promotion on FAIL (park filtering; do not touch other experiments).

## Budget

CPU-only, < 20 min wall (dominated by 4× `score.py` Hungarian matching;
the 26k-node sample is the slow one). No GPU, no pip, no Kaggle calls.
