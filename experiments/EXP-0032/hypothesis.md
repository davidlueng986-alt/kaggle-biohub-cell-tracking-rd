# EXP-0032 — Training patch export

## Hypothesis
A deterministic, CPU-cheap patch export (cell-centred 3D positives from GT
nodes + 1:1 hard negatives from cheap max-filter bright maxima and random
background) produces a balanced, sub-2 GB training set on the 6-sample subset
that unblocks FUTURE GPU work on a learned detector / learned edge classifier
— the documented residual after classical DoG recall ceilings (EXP-0021/24)
and uninformative classical appearance (EXP-0015/16).

## Background
- PROTOCOL v1.1 (`docs/PROTOCOL.md`): embryo-grouped CV (fold0 holdout 44b6,
  fold1 holdout 6bba); trusted scorer `scripts/score.py`; metric
  `score = adjusted_edge_jaccard + 0.1 * division_jaccard`, 7 µm match,
  voxel z=1.625/y=x=0.40625.
- `knowledge/STATE.md` H-003 notes + next-steps: learned features are the
  residual direction. This experiment is the enabling rung (no training).
- GT graphs: `experiments/EXP-0003/gt/<sid>_gt.json`; images:
  `data/train/<sid>.zarr` uint16 (T,Z,Y,X) ~ (100,64,256,256).

## Falsification criteria
- FAIL if export exceeds 25 min or 2 GB, or balance deviates from 1:1 by >5%.
- FAIL if spot-checks reject patch quality: <18/20 random positives with
  center-box mean > full-patch mean, or positives vs negatives statistically
  indistinguishable (Welch p >= 0.01).
- (Design doc `train_design.md` is not falsifiable here — it is reviewed, not run.)
