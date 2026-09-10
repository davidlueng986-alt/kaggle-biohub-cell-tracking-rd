# EXP-0040 — Replicate @96 dark-sample recall gain on 0b24845f + 0c582fdc full-video

## Hypothesis

Lowering the DoG detection percentile from 99.0 to 96.0 on the full 100-frame
44b6_0b24845f and 44b6_0c582fdc videos raises node recall by >= 0.10 over the
@99.0 full-video bars WITHOUT lowering the adjusted edge jaccard — i.e. the
EXP-0039 GO result on 6bba_05db0fb1 (recall 0.29->0.68, adj 0.209->0.482)
generalizes to the other two dark samples.

## Background

- PROTOCOL v1.1 (frozen): score = adjusted_edge_jaccard + 0.1*division_jaccard;
  node match 7 um; voxel z=1.625/y=x=0.40625; trusted scorer scripts/score.py
  v1.1.0.
- Prior: EXP-0039 GO — single-sample evidence (05db0fb1 only), needs replication.
- Baselines (EXP-0021 rows, full-video @99.0; recomputed-by-rescoring in this EXP):
  0b24845f rec 0.325 adj ~0.104; 0c582fdc rec 0.197 adj ~0.096.
- GT: experiments/EXP-0003/gt/44b6_0b24845f_gt.json (T_true=32795),
  experiments/EXP-0003/gt/44b6_0c582fdc_gt.json (T_true=27958).

## Falsification criteria

- Per-sample REPLICATES iff recall(@96) >= recall(@99 bar) + 0.10
  AND adj(@96) >= adj(@99 bar). Else DIVERGES (record direction + T_ratio +
  det/frame for the mechanism note).
- Overall: 2/2 REPLICATES -> GO (recommend @96 as dark-sample policy rung
  EXP-0041, do not run); 1/2 -> MIXED (sample-specific, note which);
  0/2 -> STOP (@96 does not generalize beyond 05db0fb1).
