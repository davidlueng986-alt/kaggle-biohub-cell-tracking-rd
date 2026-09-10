# Notes — EXP-0022 Downsample parity + MAD probe (H-002/H-005)

## Log
- 2026-09-09/10: `bash experiments/EXP-0022/run.sh` → exit 0, GO True.
- MAD-pure falsified at probe (t25): thr 3.8–7.8 vs pct-thr 60; FEWER
  detections (24–32 vs 45) with recall 5–6/8 vs 8/8. Mechanism: whole-frame
  MAD sits at background-noise scale → threshold near background → giant
  merges → size-filter drops/displaces. No window matrix spent (correctly —
  a rule that loses on its best frame is dead). Hybrid (MAD floor under
  percentile) would just revert to percentile; not pursued.
- Downsample (half-res y/x, centroids ×2, no refine):
  window rec IDENTICAL 0.982, linked ec IDENTICAL 143/2/5 (raw 0.9533),
  adj UP 0.9804→0.9949 (fewer unannotated extras → bigger bonus), det
  911→718 (−21%), timing 0.83→**0.22 s/f (3.8×)**. The 193 lost detections
  never participated in GT links — pure clutter removal by accident of
  scale. Anchor A==EXP-0013A exact ✓.
- H-005 impact: detection drops from dominant cost (84–205 s/video) to
  ~22 s/video. Hidden projection reframes from ~18 h to roughly
  detection-minor + linking-dominated (linking cost next to profile on
  full video; Hungarian O(n³) per pair is the new bottleneck candidate).

## Decisions
- `keep-trying` — GO: EXP-0023 full-video DS (6bba + 44b6 control) with edge
  + timing readouts, then kernel upgrade path (notebook DS switch) if it
  holds. Standing policy adds a timing dimension, not yet a level change.
- Next: EXP-0023 full-video DS both samples (H-002/H-005).
