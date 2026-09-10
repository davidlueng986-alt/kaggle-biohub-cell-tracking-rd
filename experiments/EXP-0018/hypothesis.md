# EXP-0018 — Gate-10 jitter replication (H-002)

## Hypothesis

EXP-0017's gate-10 win (FN 55→5 for 1 FP, both folds up, div-neutral) is a
stable property of fast-cell motion (7–10 µm pairs), not a knife-edge of
exact voxel coordinates: under σ=0.3 vox jitter seeds {0,1,2}, gate-10
holds no-regression vs floor on both folds in all seeds, keeps division
FP=0 (neutrality replicates — the single 05db0fb1 FP must not multiply),
and beats-or-ties its noise-matched gate-7 base in ≥2/3 seeds. Pre-registered
promotion rule (§4): PROMOTE gate-10 to new best (worst-fold 1.0884) iff
(a) EXP-0017 unperturbed numbers stand (b) all 3 seeds: fold0 ≥ floor AND
fold1 ≥ floor (c) div FP=0 every seed (d) LOO same-set head-to-head passes.
Fail any → keep-trying (candidate status kept or revoked per evidence).

## Falsification criteria

- REVOKE candidacy (back to variant pool) if any seed regresses either fold
  vs floor, or div FP appears under noise (neutrality was the promotion
  case), or LOO same-set fails.
