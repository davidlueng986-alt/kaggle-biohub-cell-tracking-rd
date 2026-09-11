# Notes — EXP-0056 05db0fb1 @95.0 descent probe

## Log

- Created via scripts/new_experiment.sh (EXP-0056 confirmed free; max was EXP-0055).
- Reference bars verified by reading (not pasting): EXP-0055/metrics.json
  (@95.5: recall 0.7135077, adj 0.5158580, T_ratio 0.6207 — the bar to beat;
  frozen @96.0 recall 0.6756/adj 0.4822; frozen @98.5 recall 0.2903/adj 0.2092).
- EXP-0009 has no 05db0fb1 row (44b6_0113de3b + 6bba_05b6850b only);
  EXP-0011 ran 6bba_05b6850b only — both correctly excluded from the 05db0fb1
  descent comparison.
- run.sh + score_fast.py adapted from the EXP-0055 pattern (pct 95.5 -> 95.0,
  score key p955 -> p950, frozen @95.5 row added to comparison).
- (run log appended after execution)
- Smoke t=0 @95.0: 456 dets, 0.64 s (denser than @95.5 avg 433.2/f — monotonic).
- Full run OK: detect 100/100 frames; equivalence gate passed (t=0/20/50/99);
  link 44320 gid-unique nodes; trusted score 2.0 s; wall 21.9 s (score stage).
- Result @95.0: recall 0.7500, det/f 443.20, raw 0.5273, adj 0.5466, div 0.0,
  score 0.5466, ec TP704/FP152/FN479, dc 0/0/3, T_ratio 0.6350, s/f 0.6599.
- Deltas vs @95.5: d_recall +0.0365, d_adj +0.0307 → CONTINUE-DESCENT
  (both meet-or-beat bars 0.7135 / 0.5159). Parity watch: T_ratio 0.6350,
  approaching but still below ~0.65 watch level.

## Decisions

- Reuse EXP-0055 pipeline verbatim apart from pct: same detector CLI, same
  BL.link defaults (gate 7um, image-side policy unchanged), same trusted
  scorer with runtime-only equivalence-gated scipy solver. scripts/* untouched.
