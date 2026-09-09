# Notes — EXP-0001 Embryo-CV baseline harness

## Log

- Created via `scripts/new_experiment.sh EXP-0001 "Embryo-CV baseline harness"`.
- Filled hypothesis.md (H-001 link + falsifiable prediction), plan.md
  (toy fold configs, hand calcs, cold-run steps), run.sh (scorer --dry-run +
  toy pred/gt through `score.py --pred --gt --out` + metrics.json merge).
- Ran `bash experiments/EXP-0001/run.sh` and `bash scripts/run_loop.sh --dry-run`.

## What learned

- `bash experiments/EXP-0001/run.sh` → exit 0. Scorer `--dry-run` OK;
  fold0-toy score **0.600** (edge 0.5, div 1.0 — matches hand calc exactly,
  `hand_calc_match_fold0: true`); fold1-toy score **0.3333** (edge 1/3,
  div 0.0 — deliberate division miss behaves as designed).
- `bash scripts/run_loop.sh --dry-run` → exit 0 AFTER one scaffold fix (below).
  No GPU, no data, stdlib only. Full metrics in `metrics.json` (`dry_run: true`).
- Scaffold bug found: `experiments/EXP-0000/` (template) shipped without
  `metrics.json`, but `run_loop.sh` requires valid `metrics.json` in every
  `EXP-*/` dir → loop failed with `FAIL: experiment .../EXP-0000/ missing
  metrics.json`. Fixed by adding a clearly-marked template placeholder
  `experiments/EXP-0000/metrics.json` (`scores: null`, template note) rather
  than weakening the runner's validation gate.
- README/STATE `.py → .sh` runner references were already corrected by a
  concurrent agent (verified: README lines 35/38/41, STATE lines 25/33/66
  all say `run_loop.sh`); no edit needed from this experiment.

## Decisions

- Decision recorded in `metrics.json`: `keep-trying` (dry-run harness, not evidence
  for/against H-001's transfer claim).

## Next

- Publisher: append EXP-0001 row to `knowledge/RESULTS.md`; flip H-001
  `backlog → active` in `knowledge/HYPOTHESES.md` once ledger updated.
- EXP-0002 (blocked on Kaggle auth + data): real embryo-CV baseline —
  DoG+Hungarian sanity on fold0 holdout `44b6` vs fold1 `6bba`, ≥2 seeds,
  full geff scorer swap per `score.py` TODO + PROTOCOL §1, then freeze.
- Open TODOs carried from PROTOCOL v1.0: µm scaling constants, `T_true`
  provenance, `submission.csv` schema.
