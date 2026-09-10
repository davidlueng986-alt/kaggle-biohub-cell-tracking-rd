# Plan — EXP-0040 Replicate @96 dark-sample recall gain on 0b24845f + 0c582fdc full-video

## Config / seeds

- Deterministic detector CLI defaults; only `--pct 96.0` varies from the
  @99.0 bars. No seeds (detector + linker deterministic).
- Data: data/train/44b6_0b24845f.zarr + data/train/44b6_0c582fdc.zarr,
  frames t=0..99 (100 each, ~200 frames total).
- Linker: baseline_link defaults (gate 7 um, one-to-one, causal); globally
  unique ids per video (det files restart ids per frame -> reassign gid).
- Scorer: trusted scripts/score.py v1.1.0 via score_fast.py runtime-only
  scipy solver swap (equivalence-gated; scripts/* unmodified on disk).
- GT T_true: 0b24845f=32795, 0c582fdc=27958 (asserted at score time).

## Steps

1. Run `./experiments/EXP-0040/run.sh` (detect -> link -> score -> metrics.json).
2. Score with trusted scorer: `score_fast.py` calls
   `score.score_samples([(sid, pred, gt, None)])` for @96 preds + fresh
   rescore of frozen EXP-0021 @99 preds (bars never pasted).
3. Verdicts computed in run.sh step 4/4 per falsification criteria.

## Budget

CPU-only, < 35 min: ~200 frames detection (~1.2 s/frame, ~5-8 min) + link/score.
