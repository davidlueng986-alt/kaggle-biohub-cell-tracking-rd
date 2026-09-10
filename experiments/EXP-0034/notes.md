# Notes — EXP-0034 Per-sample-best transfer test

## Log
- 2026-09-10: `bash experiments/EXP-0034/run.sh` → exit 0, 780.8 s wall
  (~0.67 s/frame detect; linking+scoring the remainder). 300 detections
  (3 samples x 100 frames) at EXP-0024 best pcts, frozen DoG
  (1,3,3)/(1.6,5,5), min-size 50, percentile thr-mode. Global gid re-id per
  video, baseline_link, full-video score via score.py CLI (true T_true),
  window-slice (t20-29) linked score + recalls in-process.
- Determinism check passed: window recalls recomputed from the same
  detections match EXP-0024 refs bit-exact (0.8000 / 0.5000 / 0.4056).
- Per-sample window → full (recall micro; edge adj):
  - 44b6_0b24845f @98.5: rec 0.8000 → 0.4314 (d=-0.3686); edge 0.5476 →
    0.2249 (d=-0.3227). BREAKS, direction recall_down + edge_down.
    Full: TP/FP/FN 12/7/37, div 1.0 (no GT divs), score 0.3249,
    T_pred/T_true 16493/32795, det/f 164.9.
  - 44b6_0c582fdc @97.5: rec 0.5000 → 0.4930 (d=-0.0070); edge 0.3280 →
    0.2767 (d=-0.0513). TRANSFER-HOLDS. Full: 21/9/49, div 1.0,
    score 0.3767, T 16531/27958, det/f 165.3.
  - 6bba_05db0fb1 @97.5: rec 0.4056 → 0.4784 (d=+0.0728); edge 0.2798 →
    0.3367 (d=+0.0568). TRANSFER-HOLDS (both drift UP). Full: 415/112/768,
    div 0.0 (3 GT divs, one-to-one linker finds none), score 0.3367,
    T 34455/69800, det/f 344.6.
- Aggregate: 2/3 HOLDS → STOP.

## Decisions
- STOP: window selection does not transfer reliably — 0b24845f's window
  (10 GT nodes) overstated recall by 0.37 and edge by 0.32 vs full video
  (51 GT nodes, t11-50). Per-video calibration must be full-video or
  learned; do NOT promote window-selected per-sample levels to an
  EXP-0035 full-subset policy.
- Nuance for the record: transfer is sample-dependent, not uniformly
  broken — 0c582fdc held almost exactly, 05db0fb1 improved off-window.
  The failure mode is small-window sampling noise + detector-blind cells
  outside the window (cf. EXP-0024: 2/10 window GT nodes unmatched at ANY
  pct), not a systematic level shift (det/f full ≈ window: 164.9 vs 155.0).
- Window-implied edge definition (hypothesis/plan): EXP-0024 built no
  window edges, so the implied level is the linked+scored t20-29 slice of
  the same detections (same linker, same true T_true). Raw edge + |full_adj − window_recall| recorded in metrics.json for transparency.

## Unexpected observations
- Detection ran ~3-6x faster than EXP-0024 pace (0.67-0.68 s/f vs 2-4 s/f)
  at identical settings — same vectorized code path; difference is machine
  load variance, not a settings change (window recalls reproduce exactly).
- 44b6 GT spans are short (0b24845f t11-50, 0c582fdc t20-90) vs 100-frame
  video: full-video scoring matches per-t, out-of-GT frames contribute
  detections (T_pred) but no matchable GT — T_true adjustment absorbs this
  (all T_ratios 0.47-0.59, factors >1).
