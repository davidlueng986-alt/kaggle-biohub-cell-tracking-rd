# EXP-0021 — Image-policy transfer, all 6 subset samples (H-002)

## Hypothesis

Per-embryo DoG levels transfer within embryo: 44b6×3 @99.0 all reach
recall ≥ 0.95 with edge character like 44b6_0113de3b (sparse, clean), and
6bba×3 @98.5 all reach recall ≥ 0.85 with edge in the 0.65–0.90 band —
because levels key on embryo intensity regime (frame-mean ~219 vs ~82),
not on sample idiosyncrasy. Reuses frozen EXP-0008/0009 detections for the
two reference samples (verified by spot re-detection assert on positions —
schema evolved with split/parent keys since; timing excluded as noise) and detects
the other four fresh. Result is the full-subset IMAGE baseline (embryo
micros + worst-fold) that future image rungs must beat; oracle best
(1.0884) stays the overall reference. Division readout appears where GT
divs exist (05db0fb1 ×3, 062c8d37 ×1; one-to-one links → expect div 0 with
FNs — the standing H-003 gap on the image path). Ceiling keep-trying
(baseline rung, single deterministic pass).

## Falsification criteria

- REJECT transfer if any sample misses its embryo recall bar (then levels
  are sample-specific → per-sample tuning or adaptive threshold needed).
- REJECT artifact reuse if spot re-detection differs by even one voxel
  in POSITIONS (determinism breach → re-detect everything, bug-hunt first;
  dict-schema evolution and timing noise excluded by construction).
