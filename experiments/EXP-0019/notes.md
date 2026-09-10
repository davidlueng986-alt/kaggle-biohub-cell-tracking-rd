# Notes — EXP-0019 Gate-10 + r10 combo (H-002/H-003)

## Log
- 2026-09-09: `bash experiments/EXP-0019/run.sh` → exit 0, all 4 checks pass.
- Combo (gate-10 base + r10 proposals, 3 fork extras, all on 6bba):
  - fold0 44b6: micro identical to best (extra=0 everywhere — clean tissue
    proposes nothing, evidence rule holds).
  - fold1 6bba: micro 1.0884 → **1.0895** (+0.0011); div 0/0/4 → **3/0/1**
    (ALL THREE proposals are TPs with FP=0 — including the 9.08 µm boundary
    pair that flickered in EXP-0006: gate-10 links repositioned the geometry
    in its favor).
  - Mechanism bonus: fork edges matching GT division edges count as edge
    TPs too (05db0fb1 1179→1181 TP, FN 4→2; FP stays 1).
- Debug incident: first verdict run compared against ROUNDED literal micros
  (1.0998/1.0884) and falsely failed fold0 on float dust; fixed to recompute
  the bar from frozen EXP-0017 grid.json (1.099790/1.088402). Lesson: bars
  are recomputed from artifacts, never pasted decimals (applies to every
  future gate — added to run-book below).

## Decisions
- `keep-trying` — combo PASSES the bar → promotion CANDIDATE (not a
  promotion: single deterministic pass). r10's standalone candidacy is now
  subsumed (combo strictly dominates it: same forks + better base).
- Next: EXP-0020 replication for the combo (jitter {0,1,2} + matched
  gate-10 base + LOO, same pre-registered bar shape as EXP-0018). Pass →
  combo PROMOTES (worst-fold 1.0895, div 3/0/1).

## Run-book addition (binding on future rungs)

- Recompute every comparison bar from frozen artifacts inside run.sh;
  rounded decimals in prose are display-only and must never gate.
