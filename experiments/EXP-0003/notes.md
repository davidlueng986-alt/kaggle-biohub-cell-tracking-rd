# Notes — EXP-0003 Real-data oracle-linker baseline (subset 6)

## Log
- 2026-09-09: subset download DONE (738/738, 2.6 GB); scaffolded via `new_experiment.sh`.
- 2026-09-09: `bash experiments/EXP-0003/run.sh` → exit 0.
- Per-sample (v1.1, T_true pinned from geff):
  - 44b6_0113de3b: edge 1.0778 / div 1.0000 (no GT divs) / 1.1778 (49/0/1)
  - 44b6_0b24845f: edge 1.0998 / div 1.0000 / 1.1998 (49/0/0)
  - 44b6_0c582fdc: edge 1.0997 / div 1.0000 / 1.1997 (70/0/0)
  - 6bba_05b6850b: edge 1.0800 / div 1.0000 (no GT divs) / 1.1800 (840/0/5)
  - 6bba_05db0fb1: edge 1.0778 / div 0.0000 (3 GT divs missed) / 1.0778 (1161/0/22)
  - 6bba_062c8d37: edge 1.0520 / div 0.0000 (1 GT div missed) / 1.0520 (871/0/27)
- Embryo micro-edge: 44b6 = 1.0933, 6bba = 1.0705, worst-fold = 1.0705.
- Division sums: TP 0 / FP 0 / FN 4 (linker emits no forks — invariant holds).
- Edge > 1.0 throughout = spec-legal under-prediction bonus (T_pred << T_true),
  NOT a bug. Oracle detections + near-perfect linking still miss 55 GT edges
  (motion beyond 7 µm or adjacent-frame gaps).

## EDA + leakage check (GOLD §2)
- Embryo grouping confirmed: folder prefixes 44b6 ×3 / 6bba ×3; evaluated per
  embryo, never pooled for promotion. No cross-embryo state in linker.
- Sparse GT confirmed: 44b6 samples 51–71 nodes vs T_true 25–33k; 6bba
  861–1229 nodes vs T_true 6k–70k. Voxel scale confirmed in geff attrs
  (z 1.625 / y,x 0.40625) — matches COMPETITION.md, no doc change needed.
- Causality: adjacent-frame links only, no future-frame use.

## Decisions
- `keep-trying` — this is the floor (oracle detections, zero training). Next:
  EXP-0004 image-based detection probe (DoG on 1–2 zarr timepoints, CPU) or
  linker variant that proposes forks (division sub-gate: needs div gain with
  no edge regression on BOTH folds). Notebook skeleton path after that.
