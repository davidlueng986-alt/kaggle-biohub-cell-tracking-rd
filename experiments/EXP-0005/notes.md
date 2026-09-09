# Notes — EXP-0005 Radius ablation × isolation (H-002+H-003)

## Log
- 2026-09-09: `bash experiments/EXP-0005/run.sh` → exit 0. Grid
  r∈{9,10,11,12} + isolation at r=10/15; all 6 scored with v1.1.
- Ablation (micro-edge deltas vs EXP-0003 floor 44b6 1.0933 / 6bba 1.0705):
  - r9:  fold1 +0.0004, div 1/0/3, gate True  (under-recovers: misses 9.08 µm pair)
  - r10: fold1 +0.0011, div 3/0/1, gate True  ← SELECTED (plateau, FP=0)
  - r11: identical to r10 (plateau confirmed)
  - r12: fold1 +0.0008, div 3/1/1, gate True  (first FP appears)
  - r10+iso: identical to r10 (veto never fires at tight radii)
  - r15+iso: fold1 −0.0011, div 4/7/0, gate False (recovers all 4 GT divs but 7 FPs;
    isolation veto helped vs r15-off's 10 FPs yet still fails)
- fold0 44b6 byte-identical across the whole grid (no proposals; 0 GT divs).
- Selection: r10 (gate pass → worst-fold → smallest radius).

## Decisions
- `keep-trying` — sub-gate numeric PASS for r10, but §4 gate 1 needs a fold0
  win (impossible: 44b6 has 0 GT divisions, floor is exactly matched) plus
  multi-seed replication of a deterministic pipe. r10 designated
  **ensemble-candidate** (diverse error profile: +3 div TPs at zero edge
  cost) — fusion itself must pass gates before any submit.
- Next: EXP-0006 replication rung (perturbation seeds: ±sub-voxel jitter on
  inputs; leave-one-sample-out stability) + GOLD §5 notebook skeleton with
  graphs→submission.csv writer.
