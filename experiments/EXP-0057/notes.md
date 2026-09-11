# Notes — EXP-0057 05db0fb1 @94.5 descent probe

## Log

- Created via scripts/new_experiment.sh (EXP-0057 confirmed free; max was EXP-0056).
- Reference bars read (not pasted): EXP-0056/metrics.json
  (@95.0: recall 0.7500255, raw 0.5273408, adj 0.5465910, T_ratio 0.6350 —
  the bar to beat; frozen @95.5 recall 0.7135/adj 0.5159; frozen @96.0
  recall 0.6756/adj 0.4822; frozen @98.5 recall 0.2903/adj 0.2092).
- run.sh + score_fast.py adapted from the EXP-0056 pattern (pct 95.0 -> 94.5,
  score key p950 -> p945, frozen @95.0 row added, bars 0.750/0.5466, deltas vs @95.0).
- Smoke t=0 @94.5: 464 dets, 0.65 s (denser than @95.0 t=0 456 — monotonic).
- Full run OK: detect 100/100 frames (44896 dets, 448.96/f); equivalence gate
  passed (t=0/20/50/99); link 44896 gid-unique nodes, 38236 edges [scipy];
  trusted score 2.1 s; score-stage wall 23.4 s.
- Result @94.5: recall 0.7635, det/f 448.96, raw 0.5211, adj 0.5397, div 0.0,
  score 0.5397, ec TP705/FP170/FN478, dc 0/0/3, T_ratio 0.6432, s/f 0.6522.
- Deltas vs @95.0: d_recall +0.0135 (OK), d_raw -0.0063, d_adj -0.0069 (FELL)
  → STOP-DESCENT (recall bar 0.750 met, adj bar 0.5466 missed).
- Turn mechanism: edge TP only +1 (704→705) while FP +18 (152→170) — extra
  detections attach near already-matched GT nodes and mint spurious edges
  (merging/displacement regime); raw jaccard fell despite recall rising.
  Parity watch: T_ratio 0.6432, closing on the ~0.65 watch level.

## Decisions

- Reuse EXP-0056 pipeline verbatim apart from pct: same detector CLI, same
  BL.link defaults (gate 7um, image-side policy unchanged), same trusted
  scorer with runtime-only equivalence-gated scipy solver. scripts/* untouched.
- Descent on 05db0fb1 stops here: @95.0 remains the operating point; do NOT
  probe lower pct on this sample without a new hypothesis (e.g. linker-side
  merge handling rather than denser detection).
