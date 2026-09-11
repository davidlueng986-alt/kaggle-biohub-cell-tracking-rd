# Notes — EXP-0055 05db0fb1 full-video @95.5 descent probe

## Log

- Created via scripts/new_experiment.sh (EXP-0055 was free as expected).
- Smoke probe t=20 @95.5: 457 det, thr=125.2, 0.73 s (vs 439 det / 0.69 s
  @96.0 in EXP-0039) — mild count growth, timing flat.
- run.sh executed cold end-to-end, exit 0:
  - detect 100/100 frames OK, s_f=0.6418 (vs 0.6651 @96.0).
  - link OK: 43324 nodes gid-unique, assign=scipy, gate 7um default.
  - equivalence gate passed on own @95.5 frames t=0/20/50/99
    (n_pred 440/457/448/407; matched-pair equality vs pure-python Hungarian).
  - trusted score 2.0 s; scores.json wall 20.3 s.
- scripts/* unmodified (score_fast.py does runtime-only solver swap inside
  EXP dir, same pattern as EXP-0039). No pip installs, no kaggle calls,
  no git commits. Scope respected: only experiments/EXP-0055/ written
  (+ /tmp probe file, since removed from consideration).

## Decisions

- Verdict CONTINUE-DESCENT: recall 0.7135 >= 0.68 AND adj 0.5159 >= 0.4822.
  Deltas vs frozen @96.0: d_recall +0.0379, d_raw +0.0333, d_adj +0.0337.
  Edge counts 664/153/519 (vs 620/154/563 @96.0): +44 TP, FP flat at 153
  (sparse-aware FP rule still absorbing off-target detections), FN -44.
- Parity watch: T_ratio @95.5 = 0.6207 (was 0.6015 @96.0; watch ~0.65 —
  still below parity, adjustment remains a small bonus, not a penalty).
- Division readout as expected: div 0.0, dc 0/0/3 — one-to-one linker emits
  no forks; all 3 GT divisions FN.
- det/frame 433.24 (was 419.87 @96.0, +3.2%); s/frame 0.64 (flat).
- Recall bar note: mission bar 0.68 is the rounded form of the exact @96.0
  recall 0.6756; @95.5 clears both (0.7135).
- Follow-up: descent still winning at 95.5 — next rung (e.g. @95.0) tests
  whether merging/displacement finally dominates; division-capable linker
  remains the structural gap (div 0.0, 3 FN divisions at every rung).
