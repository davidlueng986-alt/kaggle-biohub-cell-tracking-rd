# Plan — EXP-0002 Full-scorer geometric validation

## Config / seeds

- Hypothesis: H-001 + H-004 (`knowledge/HYPOTHESES.md`).
- Protocol: `docs/PROTOCOL.md` FROZEN v1.1 (do NOT edit).
- Scorer: `scripts/score.py` v1.1.0 (numpy + stdlib, no GPU, no data).
- Seeds: n/a (deterministic geometry; no randomness).
- Voxel: default `1.625,0.40625,0.40625`; max-dist 7.0 µm.
- Folds (toy geometric stand-ins, NO real data):
  - fold0 (holdout `44b6` stand-in, promotion fold): linear chain
    t0→t1→t2 at (z32,y128,x128) with 1-voxel drift (matches within 7 µm).
    GT `T_true` = 3 (pinned).
  - fold1 (holdout `6bba` stand-in, stability check): 2-node chain + division
    probe (parent→2 daughters→grands), `T_true` pinned.
- Variants per fold: `perfect`, `idswitch` (wrong edge, same endpoints class),
  `inflated` (extra nodes, same true edges).

## Cold-run steps

1. `bash experiments/EXP-0002/run.sh`
   - Writes `fold{0,1}_{perfect,idswitch,inflated}_{pred,gt}.json`.
   - Scores each pair via `python3 scripts/score.py --pred ... --gt ... --out ...scores.json`.
   - Merges into `metrics.json` (envelope: `exp_id`, `hypothesis_id`,
     `protocol_version: 1.1`, `scorer_version`, `dry_run:true`,
     `simplified_scorer:false`, `checks` booleans, `decision`).
   - Asserts: perfect total == 1.1; idswitch FP ≥ 1 and score < perfect;
     inflated adjusted < perfect adjusted.
2. `bash scripts/run_loop.sh --dry-run` (validates all EXP metrics.json).
3. Both must exit 0.

## Budget

- CPU-only, stdlib+numpy, seconds. No Kaggle download, no training.
- Real-run note (EXP-0003+): 12 h T4 code-competition limit, ≈80–96 s/video;
  record `infer_s_per_video` once real inference exists.
