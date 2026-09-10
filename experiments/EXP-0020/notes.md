# Notes — EXP-0020 Combo replication (H-002/H-003)

## Log
- 2026-09-09: `bash experiments/EXP-0020/run.sh` → exit 0, KEEP verdict.
- Seeds: seed1/2 replicate fully (folds ≥ best AND ≥ matched base, div
  3/0/1, efp==1); seed0 misses fold1 by 4e-4 (1.0880 vs 1.088402) with div
  2/0/2 — the predicted boundary-pair flicker (9.08 µm vs 10 µm radius).
  Safety replicates perfectly: div FP==0 and edge FP==1 in all seeds
  (zero growth); LOO same-set clean (no notes).
- The miss is narrow but the bar was pre-registered strict for a reason:
  promotion-grade claims need margin, and the combo's div upside is
  probabilistic under detection noise (2–3 TPs) while its edge sits within
  noise of best. A 4e-4 shortfall on 1/3 seeds is exactly what the bar
  exists to catch.
- LOO bug from the first attempt (helper iterated all SIDS incl. the
  dropped key) fixed to iterate remaining rows — second methodology bug of
  this class after EXP-0006's floor-comparison bug. Rule reinforced:
  head-to-head comparisons iterate the SHARED set.

## Decisions
- `keep-trying` — promotion DENIED; candidacy REVOKED as promotion
  contender per the pre-registered rule (regression on seed0), narrowly
  (4e-4, flicker class). Configuration retained in the variant pool with
  its numbers intact — re-nomination needs a sturdier margin.
- Forward link: the flickering TP is the boundary pair — precisely the case
  for jitter-invariant confirmation (H-003 appearance evidence would not
  flicker under coordinate noise). Combo + appearance confirmation is the
  principled re-nomination path (EXP-0022+).
- Next: EXP-0021 image-policy transfer (per-embryo levels across all 6
  subset samples + link + embryo micros) — the submittable path is where
  promotable gains now live; oracle arm holds at gate-10 best.
