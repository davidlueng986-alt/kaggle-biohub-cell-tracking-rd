# EXP-0001 — Embryo-CV baseline harness (H-001)

## Hypothesis (H-001 — Embryo-CV trusted baseline)

With only 2 train embryos (`6bba`, `44b6`), embryo-grouped CV is the only
honest scorer; frame-random splits leak embryo identity and overfit.
See `knowledge/HYPOTHESES.md` H-001 and `docs/PROTOCOL.md` §2 (folds),
§4 (promotion gates).

## Prediction (falsifiable)

1. The frozen SIMPLIFIED scorer (`scripts/score.py`) runs end-to-end on toy
   pred/gt JSON with no data download and no GPU, producing
   `score = adjusted_edge_jaccard + 0.1 * division_jaccard` per toy fold.
2. A toy fold pair modelled on the embryo-CV design (fold0 holdout `44b6`,
   fold1 holdout `6bba`) yields finite, auditable scores recorded in
   `metrics.json` with `dry_run: true`.
3. `bash experiments/EXP-0001/run.sh` and `bash scripts/run_loop.sh --dry-run`
   both exit 0.

## Falsification criteria

- REJECT the harness if either command exits non-zero, if `metrics.json`
  cannot be produced from real scorer output, or if the scorer's toy
  computation disagrees with hand calculation (fold0 edge-Jaccard must be
  exactly 0.5 on the toy sets below; any deviation = scorer bug per
  PROTOCOL §1 → fix, bump protocol version, re-score).
- This experiment does NOT test the H-001 transfer claim
  (embryo-CV < frame-split but transfers to LB) — that needs real data
  (blocked: no Kaggle auth, no GPU). Outcome here only validates the
  scoring/loop plumbing the real test will run through.
