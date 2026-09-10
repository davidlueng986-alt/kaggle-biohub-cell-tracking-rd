# EXP-0020 — Combo replication (H-002/H-003)

## Hypothesis

EXP-0019's combination (gate-10 base + r10 proposals: fold1 +0.0011, div
3/0/1, fold0 identical) replicates under σ=0.3 vox jitter seeds {0,1,2}:
no-regression vs the recomputed best (gate-10 micros from frozen EXP-0017
grid — never rounded literals, EXP-0019 run-book rule) on both folds in
all seeds; division TP ≥ 2 with FP == 0 every seed (boundary pair may
flicker as in EXP-0006 — gain-with-safety replicates even then);
variant ≥ noise-matched gate-10 base both folds every seed. Pre-registered
promotion rule: PROMOTE combo to new best (worst-fold 1.0895, div 3/0/1)
iff (a)+(b)+(c) hold in all seeds plus (d) LOO same-set head-to-head
(combo-unperturbed vs best) passes. Fail any → keep-trying (candidate kept
if safety replicates, i.e. FP==0 + no-regression; revoked only on
regression or FP growth).

## Falsification criteria

- REVOKE candidacy (variant pool) on any seed regressing either fold vs
  best, any div FP under noise, or LOO same-set failure.
