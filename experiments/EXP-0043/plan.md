# Plan — EXP-0043

1. Verify next free id (EXP-0043 free) + scaffold via scripts/new_experiment.sh.
2. Calibrate: single-frame detect t=20 @96.0 on 6bba_062c8d37.zarr
   (expect ~50-70 det, < 1 s).
3. Full-video detect t=0..99 @96.0 (python3 scripts/dog_detect.py
   data/train/6bba_062c8d37.zarr --t <T> --pct 96.0 --out ...).
4. Global re-id (per-frame ids restart -> assign gid 1..N) + BL.link
   defaults (gate 7 um; do NOT widen per image policy).
5. Score both arms with trusted score.py (true T_true=6030):
   @96.0 fresh pred; @98.5 frozen EXP-0021 pred rescored fresh.
   Small-N sample -> pure-python Hungarian runs directly, no swap.
6. Verdict per gates (recall >= 0.90 AND adj >= bar) -> REPLICATES /
   MIXED / DIVERGES; policy GO only on REPLICATES else STOP.
7. Write hypothesis.md, plan.md, notes.md, metrics.json, run.sh,
   score_run.py, scores.json under experiments/EXP-0043/ only.

Budget: CPU-only, deterministic, < 30 min (~1 min detect + link/score).
Scope: CREATE under EXP-0043 only; READ anywhere; no scripts/docs/
knowledge/other-experiments/data-patches edits; no pip; no kaggle;
no git commits.
