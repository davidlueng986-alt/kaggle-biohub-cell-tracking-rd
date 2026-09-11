# EXP-0057 — 05db0fb1 full-video @94.5 descent probe

## Hypothesis

Continuing the percentile descent below 95.0 (to 94.5) on the dense+dim
sample 6bba_05db0fb1 still improves recall faster than merging/displacement
costs accrue, i.e. full-video adjusted edge Jaccard at @94.5 meets-or-beats
the @95.0 operating point.

## Background

- Descent so far on 05db0fb1 (dense+dim, T_true=69800, 3 GT divisions),
  all full-video, same linker/scorer:
  @98.5 recall 0.290 / adj 0.209 (frozen row via EXP-0021/EXP-0039) ->
  @96.0 recall 0.676 / adj 0.482 (EXP-0039) ->
  @95.5 recall 0.7135 / adj 0.5159 (EXP-0055, verdict CONTINUE-DESCENT) ->
  @95.0 recall 0.7500 / adj 0.5466 (EXP-0056, verdict CONTINUE-DESCENT).
- Mechanism: the sparse-aware FP rule ignores off-target detections while
  extra true matches drive edge TP; descent wins until merging (two cells
  fusing into one detection) and centroid displacement dominate.
- Linker fixed: baseline_link defaults (gate 7um, one-to-one, causal), so
  div is structurally 0.0 (3 GT divisions all FN) at every rung.

## Falsification criteria

- CONTINUE-DESCENT iff recall >= 0.750 AND adj >= 0.5466 (both meet-or-beat
  the @95.0 bar, mission-spec).
- STOP-DESCENT if either falls (merging/displacement dominates at 94.5 —
  descent turned).
- This rung is a single-sample operating-point test (NOT a promotion claim):
  single deterministic pass, HP fixed a priori at 94.5, no selection on this
  sample. Promotion claims remain governed by the v1.2 trusted envelope
  (cv_tag, nested HPs).
