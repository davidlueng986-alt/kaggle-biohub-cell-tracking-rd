# Notes — EXP-0023 Full-video DS both samples

## Log

- Scaffolded via scripts/new_experiment.sh.
- DS probe t0: 44b6 124 det / 0.46 s, 6bba 43 det / 0.24 s.
- Full run: 200/200 DS detections OK; link 44b6 12287 det -> 10736 edges
  [scipy], 6bba 3727 det -> 3374 edges [pure] (backends match full-res refs).
- run.sh hit a one-line tuple-unpack bug in step-3 metrics block after
  steps 1-2 had completed; fixed (`m_n, m_d, macro = 0, 0, []`) and re-ran
  the byte-identical step-3 heredoc extracted from run.sh. Det/link/score
  artifacts stand (steps 1-2 code unchanged).
- Reference recomputation check: re-scored EXP-0008/EXP-0009 pred artifacts
  reproduce the stated bars (44b6 raw 0.9038/adj 0.9382; 6bba raw 0.7989/
  adj 0.8194, macro recall 0.8931). No pasted decimals.

## Decisions

- Verdict STOP (1/6 gates pass): no kernel upgrade.
- Key insight: EXP-0022 window parity does NOT generalize to full video.
  Window DS drops (-21% det) fell on non-GT cells; full-video DS loses
  GT-matched cells (6bba recall_micro 0.8409 vs 0.8792) and shifts centroids
  (no refine step), breaking 7um-gated links — 44b6 keeps recall 1.0 yet
  raw collapses 0.9038 -> 0.5781 (ec 47/2/3 -> 37/14/13).
- Timing path still pays: 0.45 s/f (44b6, ~4.5x) / 0.23 s/f (6bba, ~3.7x).
  Speedup is real; quality parity is the blocker.
- Suggested next: centroid refinement after x2 map-back (local full-res
  centroid in small window), then re-run this gate; or per-sample DS
  operating-point sweep before any kernel decision.

## Artifacts

- ds_<sid>_t<t>.json (200), ds_<sid>_pred.json, ds_<sid>_scores.json,
  metrics.json — all under experiments/EXP-0023/.
