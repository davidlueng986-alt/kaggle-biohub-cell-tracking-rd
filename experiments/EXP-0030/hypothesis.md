# EXP-0030 — Min-size ablation

## Hypothesis

The DoG `min-size 50` voxel floor (set once, never ablated) deletes dim but
real small cells: lowering it to 25 recovers missed GT cells (recall up)
without enough fragment-FP cost to hurt window edge scores; conversely,
raising it to 100 cuts fragment FPs but risks deleting real cells (recall
down). Predicts on the density-spanning window (t20–29 + t40–49 @98.5):
ms25 matches-or-beats the ms50 reference (A) on recall AND window edge
(raw + adj), or ms100 does so via FP reduction.

## Background

- docs/PROTOCOL.md v1.1 (frozen metric: adjusted edge Jaccard + 0.1 division;
  7um per-timepoint matching; voxel z=1.625/y=x=0.40625).
- EXP-0013 notes: fewer, better detections win (A 911 dets beats split-heavy
  configs); @98.5 reference A recomputed here as ms50.
- Gate window shared with EXP-0013/14/16 for comparability.

## Falsification criteria

- REJECT a min-size change if it falls below the recomputed ms50 (A)
  reference on ANY of recall / raw / adj on the window (then min-size
  stays 50; STOP, no full-video commit; recommend nothing).
- PROMOTE only a config >= A on all three readouts -> GO full-video
  (recommend EXP-0033, do not run here).
