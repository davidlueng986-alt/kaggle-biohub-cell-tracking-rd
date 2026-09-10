# EXP-0034 — Per-sample-best transfer test

## Hypothesis
The per-sample best DoG percentile levels found on window t=20..29 in
EXP-0024 — 44b6_0b24845f@98.5 (window recall 0.80), 44b6_0c582fdc@97.5
(window recall 0.50), 6bba_05db0fb1@97.5 (window recall 0.4056) — transfer
to full video: at the same frozen detector settings, full-video recall and
linked edge quality stay within 0.10 of their window-implied levels.

## Background
- docs/PROTOCOL.md v1.1 (frozen scorer scripts/score.py v1.1.0, embryo-level
  folds; this is a within-sample temporal-transfer probe, not a promotion
  rung).
- EXP-0024: window (t20-29) per-sample x pct recall map; best levels above.
  Scope was detection/recall-only — no window edges were built.
- EXP-0021: full-video at per-embryo levels (44b6@99.0 / 6bba@98.5) gave
  0b24845f rec 0.325 / adj 0.1040, 0c582fdc rec 0.197 / adj 0.0958,
  05db0fb1 rec 0.290 / adj 0.2092 — the gap this experiment tests is whether
  per-sample (not per-embryo) window-selected levels close the transfer gap.
- DS lesson: window-selected settings often fail full-video (brightness /
  density drift outside the window), so transfer must be measured, not
  assumed.

## Falsification criteria
Per sample, TRANSFER-HOLDS iff BOTH hold (tolerances 0.10):
1. Recall: |full_video_recall_micro − window_recall_ref| ≤ 0.10, where
   window_recall_ref is the published EXP-0024 best (0.80 / 0.50 / 0.4056).
2. Edge: |full_video_adjusted_edge_jaccard − window_slice_adjusted_edge| ≤
   0.10, where window_slice_adjusted_edge is the linked+scored edge adj on
   the t=20..29 slice of the SAME full-video detections vs the window GT
   slice (true T_true in both) — see plan.md for why this operational
   definition is used (EXP-0024 built no window edges).
Otherwise the sample verdict is BREAKS (record direction: recall and/or edge
lower/higher on full video vs window).
Aggregate: 3/3 HOLDS → GO (per-sample window-selected levels viable;
recommend EXP-0035 full-subset policy). 2/3 or worse → STOP (window
selection does not transfer; per-video calibration must be full-video or
learned).
