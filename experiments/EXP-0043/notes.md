# Notes — EXP-0043 062c8d37 full-video @96.0 replication of EXP-0039

## Log

- EXP-0043 verified free (ls showed EXP-0042 highest); scaffolded via
  scripts/new_experiment.sh.
- Calib t=20 @96.0: 59 det, thr=7.06, 0.67 s (vs @98.5 det_f 50.42 —
  density barely moves; this sample is NOT as dense as 05db0fb1).
- GT: experiments/EXP-0003/gt/6bba_062c8d37_gt.json, T_true=6030,
  930 nodes / 898 edges, 1 GT division.
- (pipeline results appended after run.sh completes)
- run.sh exit 0. Detect 100/100 frames @96.0 (~0.65 s/f).
- Link OK: 5380 nodes (gid-unique), edges per BL.link defaults, assign=pure,
  gate 7 um.
- Score: trusted score.py unmodified, pure-python Hungarian (small-N;
  score96 0.7 s-class, wall 2.2 s). @98.5 bar RECOMPUTED by rescoring
  frozen EXP-0021 6bba_062c8d37_pred.json: raw 0.8508 / adj 0.8647 /
  ec 781/20/117 — matches EXP-0021 row bit-exact.
- @96.0: recall 0.8667, det_f 53.8, raw 0.7777, adj 0.7860,
  ec TP717/FP24/FN181, T_ratio 0.8922, s_f 0.65.
- @98.5 rescored: recall 0.9301 (frozen EXP-0021 diagnostic), det_f 50.42,
  raw 0.8508, adj 0.8647, ec TP781/FP20/FN117, T_ratio 0.8362.
- Deltas (@96 - @98.5): recall -0.0634, raw -0.0731, adj -0.0787,
  score -0.0787, T_ratio +0.0561, div +0.0.
- Note the asymmetry vs EXP-0039: here lowering pct 98.5->96.0 ADDS
  detections (53.8 vs 50.42/f) yet LOSES matches (edge TP 717 vs 781,
  FN 181 vs 117). Extra sensitivity bought clutter, not cells — @96
  is not a general dense-tissue level.

## Decisions

- Verdict DIVERGES: recall FAIL (0.8667 < 0.90 gate) AND adj FAIL
  (0.7860 < 0.8647 bar). Policy STOP — EXP-0039 @96 gain was sample
  luck (05db0fb1-specific: dim dense cells below the @98.5 cutoff),
  not a transferable level. Per-sample/intensity-aware calibration
  (EXP-0022 direction) remains required.
- Division readout: div 0.0 both arms, dc 0/0/1 — one-to-one linker
  emits no forks; the 1 GT division FN as expected (standing H-003 gap).
