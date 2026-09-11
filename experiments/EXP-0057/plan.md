# Plan — EXP-0057 05db0fb1 @94.5 descent probe

## Config / seeds

- Sample: 6bba_05db0fb1, 100 frames, detector pct=94.5 (fixed a priori).
- GT: experiments/EXP-0003/gt/6bba_05db0fb1_gt.json (T_true=69800).
- Linker: baseline_link defaults (gate 7um, one-to-one, causal); globally
  unique ids across frames (det files restart ids per frame — reassign gid).
- Scorer: scripts/score.py v1.1.0 (trusted, unmodified on disk); runtime-only
  scipy solver swap inside EXP dir with equivalence gate (EXP-0056 pattern).
- Deterministic, CPU-only. No seeds (detector + linker deterministic).

## Steps

1. `bash experiments/EXP-0057/run.sh` cold end-to-end:
   - detect t=0..99 @94.5 -> full_6bba_05db0fb1_t{t}.json
   - global re-id + BL.link -> 6bba_05db0fb1_pred.json
   - `python3 -u experiments/EXP-0057/score_fast.py` -> scores.json
     (equivalence gate + recall/det diagnostics + trusted score)
   - assemble metrics.json (frozen @95.0 row from EXP-0056, frozen @95.5 /
     @96.0 / @98.5 rows via EXP-0056 — no re-detection) + verdict vs @95.0 bars.
2. Check metrics.json verdict + deltas vs @95.0.

## Budget

CPU-only, < 30 min. Expected: ~0.65 s/frame detect (~2-3 min total incl.
overhead), link seconds, score seconds, equivalence gate tens of seconds.
