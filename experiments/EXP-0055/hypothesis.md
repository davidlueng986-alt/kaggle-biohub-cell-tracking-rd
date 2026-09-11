# EXP-0055 — 05db0fb1 full-video @95.5 descent probe

## Hypothesis

Continuing the percentile descent below 96.0 (to 95.5) on the dense+dim
sample 6bba_05db0fb1 still improves recall faster than merging/displacement
costs accrue, i.e. full-video adjusted edge Jaccard at @95.5 meets-or-beats
the @96.0 operating point.

## Background

- Descent so far on 05db0fb1 (dense+dim, T_true=69800, 3 GT divisions):
  @98.5 recall 0.290 / adj 0.209 (EXP-0021 row, rescored in EXP-0039) ->
  @96.0 recall 0.676 / adj 0.482 (EXP-0039). Untested below 96.0 full-video.
- Mechanism: the sparse-aware FP rule ignores off-target detections while
  extra true matches drive edge TP; descent wins until merging (two cells
  fusing into one detection) and centroid displacement dominate.
- Linker fixed: baseline_link defaults (gate 7um, one-to-one, causal), so
  div is structurally 0.0 (3 GT divisions all FN) at every rung.

## Falsification criteria

- CONTINUE-DESCENT iff recall >= 0.68 AND adj >= 0.4822 (both meet-or-beat
  the @96.0 bar; recall bar is the mission-spec rounded form of 0.6756).
- STOP-DESCENT if either falls (merging/displacement dominates below 96).
- This rung is a single-sample operating-point test (NOT a promotion claim):
  single deterministic pass, HP fixed a priori at 95.5, no selection on this
  sample. Promotion claims remain governed by the v1.2 trusted envelope
  (cv_tag, nested HPs).
