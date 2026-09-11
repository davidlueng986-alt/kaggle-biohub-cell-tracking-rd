# Notes — EXP-0052 H-005 hidden timing calibration from v7 logs + local det artifacts

## Log
- Created via scripts/new_experiment.sh (EXP-0052 confirmed free).
- Fetched v7 log (31 records, start-to-finish: debugger warnings through
  `__results__.html` write). Per-video lines:
  44b6_0113de3b 110 s (det 15962), 44b6_0b24845f 108 s (12992),
  6bba_05b6850b 105 s (4723), 6bba_05db0fb1 114 s (26168); total 437 s =
  0.1214 h, matches kernel-reported 0.12 h.
- Hidden-rerun boundary: the downloadable log covers ONLY the 4-video
  visible run. Hidden reruns log separately and are not retrievable via the
  `kaggle kernels logs` endpoint; nothing about hidden per-video timing is
  inferred from the log itself (hidden_rerun_in_log: false).
- Cross-check: local kept-det/frame reproduces Kaggle det counts exactly
  (e.g. 159.6, 129.9, 47.2, 261.7/frame), so regimes are on the same scale.

## Decisions
- Projection uses the Kaggle-anchored model (same HW/pipeline as hidden
  rerun); local n=1000 fit (R2 0.995) justifies the linear form and shows
  the slope is small (fixed ~1.03 s/frame cost dominates on Kaggle).
- Regimes defined from observed data, not embryo labels: sparse = 46.6
  (6bba_05b6850b-like), mix = 149.6 (visible mean), dense = 261.7
  (6bba_05db0fb1-like) det/frame; +2x-dense robustness case.
- Verdict: fits — worst plausible 6.30 h (1.90x headroom); 2x-dense 6.92 h.
