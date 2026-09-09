# Plan — EXP-0001 Embryo-CV baseline harness

## Config / seeds

- Hypothesis: H-001 (`knowledge/HYPOTHESES.md`).
- Protocol: `docs/PROTOCOL.md` FROZEN v1.0 (do NOT edit).
- Scorer: `scripts/score.py` SIMPLIFIED (stdlib only, no GPU, no data).
- Seeds: n/a (deterministic set-Jaccard toy; no randomness). Real H-001 test
  will require ≥2 seeds per PROTOCOL §4 gate 1.
- Splits by embryo (toy stand-ins — NO real data touched, 87 GB NOT downloaded):
  - fold0: train `6bba` → holdout `44b6` (promotion fold). Toy:
    pred edges `[[1,2],[2,3],[3,4]]`, gt edges `[[1,2],[2,3],[4,5]]`
    → edge-Jaccard 2/4 = 0.5; divisions `[[1,2,3]]` vs `[[1,2,3]]` → 1.0;
    score = 0.5 + 0.1*1.0 = **0.6**.
  - fold1: train `44b6` → holdout `6bba` (stability check). Toy:
    pred edges `[[10,11],[11,12]]`, gt edges `[[10,11],[11,13]]`
    → edge-Jaccard 1/3 ≈ 0.3333; divisions `[[10,20,21]]` vs `[[10,20,22]]`
    → 0.0; score = 0.3333 + 0.1*0.0 ≈ **0.3333**.
    (Deliberate division miss exercises the 0.1-weighted division sub-gate.)

## Cold-run steps (another agent can run with zero setup)

1. `bash experiments/EXP-0001/run.sh`
   - Runs `python3 scripts/score.py --dry-run` (plumbing check).
   - Writes toy `fold0_pred.json` / `fold0_gt.json` / `fold1_pred.json` /
     `fold1_gt.json` into the experiment dir.
   - Scores each pair via `python3 scripts/score.py --pred ... --gt ... --out ...`.
   - Merges real scorer outputs into `metrics.json` (envelope:
     `exp_id`, `hypothesis_id`, `protocol_version`, `dry_run`, `scores`, `decision`).
2. `bash scripts/run_loop.sh --dry-run` (validates structure + all EXP `metrics.json`).
3. Both must exit 0. On failure: read the error, fix the scaffold bug inline
   (allowed: `experiments/EXP-0001/*`, `scripts/*` bugfixes needed for dry-run),
   re-run.

## Budget

- CPU-only, stdlib only, seconds of runtime. No Kaggle download, no training.
- Real-run budget note (for EXP-0002+): 12 h T4 code-competition limit,
  per-video inference ≈ 80–96 s (PROTOCOL §6–§7); `infer_s_per_video` to be
  recorded in `metrics.json` once real inference exists.
