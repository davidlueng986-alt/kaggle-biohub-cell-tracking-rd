# EXP-0056 — 05db0fb1 full-video @95.0 descent probe

## Hypothesis

Continuing the percentile descent below 95.5 (to 95.0) on the dense+dim
sample 6bba_05db0fb1 still improves recall faster than merging/displacement
costs accrue, i.e. full-video adjusted edge Jaccard at @95.0 meets-or-beats
the @95.5 operating point.

## Background

- Descent so far on 05db0fb1 (dense+dim, T_true=69800, 3 GT divisions),
  all full-video, same linker/scorer:
  @98.5 recall 0.290 / adj 0.209 (frozen row via EXP-0021/EXP-0039) ->
  @96.0 recall 0.676 / adj 0.482 (EXP-0039) ->
  @95.5 recall 0.7135 / adj 0.5159 (EXP-0055, verdict CONTINUE-DESCENT).
- Note: EXP-0011's recall-0.88/adj-0.81 @98.0 row belongs to the OTHER
  sample 6bba_05b6850b, not 05db0fb1 — excluded from this comparison.
- Mechanism: the sparse-aware FP rule ignores off-target detections while
  extra true matches drive edge TP; descent wins until merging (two cells
  fusing into one detection) and centroid displacement dominate.
- Linker fixed: baseline_link defaults (gate 7um, one-to-one, causal), so
  div is structurally 0.0 (3 GT divisions all FN) at every rung.

## Falsification criteria

- CONTINUE-DESCENT iff recall >= 0.7135 AND adj >= 0.5159 (both meet-or-beat
  the @95.5 bar, mission-spec).
- STOP-DESCENT if either falls (merging/displacement dominates at 95.0 —
  descent turned).
- This rung is a single-sample operating-point test (NOT a promotion claim):
  single deterministic pass, HP fixed a priori at 95.0, no selection on this
  sample. Promotion claims remain governed by the v1.2 trusted envelope
  (cv_tag, nested HPs).
