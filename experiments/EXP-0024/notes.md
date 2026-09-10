# Notes — EXP-0024 Per-sample threshold map

## Log
- 2026-09-10: `python3 experiments/EXP-0024/sweep.py` -> exit 0, ~436 s wall.
  150 detections (3 samples x 5 pcts x 10 frames, t=20..29), frozen DoG
  sigmas (1,3,3)/(1.6,5,5), min-size 50, match via score.match_nodes.
  Verdict NOT-RESCUED recorded in metrics.json.
- Per-sample x pct recall (matched/total over window) + det/f + s/f:
  - 44b6_0b24845f (10 GT): 97.5 0.8000/190.7/2.40 | 98.0 0.8000/176.1/2.20 |
    98.5 0.8000/155.0/1.99 | 99.0 0.5000/121.9/1.64 | 99.5 0.1000/79.3/1.17
  - 44b6_0c582fdc (10 GT): 97.5 0.5000/184.2/2.29 | 98.0 0.1000/179.4/2.29 |
    98.5 0.0000/162.3/2.04 | 99.0 0.0000/133.9/1.74 | 99.5 0.0000/94.1/1.33
  - 6bba_05db0fb1 (143 GT): 97.5 0.4056/370.7/4.18 | 98.0 0.2657/333.6/3.79 |
    98.5 0.1888/285.0/3.29 | 99.0 0.1189/221.6/2.64 | 99.5 0.0839/134.9/1.75
- Best (highest recall, ties -> lower det/f): 0b24845f @98.5 rec 0.8000
  det/f 155.0; 0c582fdc @97.5 rec 0.5000 det/f 184.2; 05db0fb1 @97.5
  rec 0.4056 det/f 370.7. All < 0.90 -> NOT-RESCUED; all three remain dark.

## Decisions
- `stop` on fixed-pct rescue: no swept level is selectable for full video on
  recall grounds (best recalls 0.80/0.50/0.41 at steep det costs). Route to
  intensity-aware calibration (MAD thr-mode / per-video self-set, cf.
  EXP-0021 diagnosis + EXP-0022) or scale-variant detection, not to wider
  percentile grids.
- Scope note (deliberate): this rung is detection/recall-only by design. The
  EXP-0012/13/14 lesson (recall without edge readout does not promote) does
  not apply to a sweep rung whose falsification criterion is a recall gate
  for selecting a level for full video; edge readout comes with the
  full-video follow-up once a level passes the gate. No level passed, so no
  edges were built.

## Unexpected observations
- 0b24845f plateaus at 0.80 across 97.5-98.5 (2/10 GT nodes unmatched at ANY
  swept level despite det/f nearly doubling 79->191): those cells are
  detector-blind at this scale, not threshold-marginal.
- 0c582fdc collapses to 0.00 at >= 98.5 (nothing annotated-cell-like in the
  top 1.5% of DoG response) yet still only 0.50 at 97.5 with 184 det/f:
  bright-clutter dominates the response tail, as EXP-0021 diagnosed.
- Cost scales with detections, not frames (05db0fb1 4.18 s/f at 97.5 vs 1.75
  at 99.5): lowering pct to chase recall multiplies H-005 timing cost while
  recall stays dark — double penalty, reinforces the stop decision.
