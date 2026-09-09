# EXP-0002 — Full-scorer geometric validation (H-001 + H-004)

## Hypothesis (H-001 embryo-CV honesty + H-004 T_true/voxel calibration)

The v1.1 faithful scorer (`scripts/score.py`, PROTOCOL v1.1) correctly
rewards geometrically true links and penalises the two classic
shake-up traps — ID switches and node-count inflation — under the real
competition pins (voxel z=1.625/y=x=0.40625 µm/voxel, 7 µm per-timepoint
matching, `T_true` penalty, division local window). See
`knowledge/HYPOTHESES.md` H-001/H-004 and `docs/PROTOCOL.md` §1.

## Prediction (falsifiable)

1. Perfect geometric tracking on toy embryo-CV folds scores **1.0 edge / 1.0 division / 1.1 total** (scores can exceed 1.0 only via under-prediction; here exact → 1.0 + 0.1×1.0 = 1.1).
2. An ID-switch variant (one wrong edge reusing annotated endpoints) yields **FP ≥ 1** and strictly lower `score` than perfect on the same fold.
3. A node-inflated variant (2× nodes, same true edges) yields strictly lower `adjusted_edge_jaccard` than perfect when `T_true` is pinned (factor 0.9).
4. `bash experiments/EXP-0002/run.sh` and `bash scripts/run_loop.sh --dry-run` both exit 0.

## Falsification criteria

- REJECT the scorer if perfect ≠ 1.1 total, if ID-switch FP = 0, or if inflation does not penalise (PROTOCOL §1 scorer bug → fix, bump to v1.2, re-score).
- This experiment does NOT test real-data transfer (no zarr download, CPU-only). Outcome validates the geometric scoring path the real embryo-CV baseline (EXP-0003+) will run through. Decision must stay `keep-trying` (harness, not promotable).
