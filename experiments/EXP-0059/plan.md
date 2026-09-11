# Plan — EXP-0059 Nested binary-darkness rule (LOSO-validated)

## Config / seeds

- Deterministic, no seeds. Gate fixed 7.0. Levels frozen: LOW=96.0, HIGH=99.0.
- Brightness B(S) = mean intensity over frames t20–29 (zarr `0` array).
- LOSO: 6 folds; fit = median B over other 5; holdout assigned dark (≤median)
  → 96.0 else 99.0. Embryo-nested: fit median on embryo A (3 samples), apply
  to all 3 of embryo B, both directions; micro-average per held-out embryo.
- Frozen det reuse (verified 100 frames each): @99 {0113de3b, 05b6850b,
  0b24845f, 0c582fdc} from EXP-0008/EXP-0021; @96 {05db0fb1} from EXP-0039,
  {0b24845f, 0c582fdc} from EXP-0040. Fresh `dog_detect.py --t T --pct P`
  only for missing (sample,pct) combos actually assigned by the rule,
  cap 300 frames total.
- Link: `baseline_link.BL.link` with globally-unique ids (det files restart
  ids per frame → reassign gid). Score: `score.score_samples` (v1.1.0);
  EXP-local scipy Hungarian swap at runtime ONLY for speed (scripts/*
  untouched), with equivalence gate vs pure-python on sampled frames.

## Steps

1. `python3 experiments/EXP-0059/brightness.py` → `brightness.json`
   (GT-free means; fit-median assignments per LOSO fold + nested directions).
2. Fresh-detect only assigned-but-missing (sample,pct) combos into
   `experiments/EXP-0059/det/` (record count ≤ 300).
3. `python3 experiments/EXP-0059/link_score.py` → per-(sample,pct,gate7)
   pred graphs + scores (reuses frozen + fresh dets).
4. Assemble `metrics.json` (cv_tag `trusted`, HP provenance per fold:
   fit set, fit median, assigned pct) + `notes.md` verdict.
5. Cold rerun: `bash experiments/EXP-0059/run.sh` (steps 1–4 end-to-end).

## Budget

CPU-only. Detection ≤ 300 fresh frames (~1–3 s/frame dense). Scoring via
scipy swap ≈ seconds. Total well under 1 h.
