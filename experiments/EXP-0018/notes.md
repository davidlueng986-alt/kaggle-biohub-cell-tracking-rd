# Notes — EXP-0018 Gate-10 replication (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0018/run.sh` → exit 0, PROMOTE verdict.
- All pre-registered conditions pass, no exceptions:
  - Seeds 0/1/2: fold0 1.0998 ≥ floor 1.0933 (the single-edge 44b6 win NEVER
    flickers — that pair sits well inside 10 µm); fold1 1.0873/1.0877/1.0877
    ≥ floor 1.0705 AND ≥ noise-matched gate-7 base (1.0675–1.0686).
  - Div 0/0/4 identical every seed (neutrality replicates perfectly).
  - Edge FP stays exactly 1 every seed (no multiplication under noise).
  - LOO same-set: no drops below floor (no notes).
- Bonus finding: gate-10 beats its noise-matched base by MORE under jitter
  (+0.019/+0.020) than clean (+0.0179) — the wider gate is more robust to
  detection noise, not less. Fast-motion pairs have margin to spare.
- Gate-10 temporaries (jit/pred/score per seed) kept in folder for audit;
  deterministic re-runnable via run.sh.

## Decisions
- **PROMOTE** — gate-10 oracle links become the new best (worst-fold
  1.0884: 44b6 1.0998 / 6bba 1.0884; div 0/0/4; FP+1 vs old floor). First
  promotion in ladder history, earned through the pre-registered bar
  (both-fold win + replication + div-neutrality + LOO), not asserted.
- Standing image policy unchanged (image side rejected widening in
  EXP-0017 arm2). r10 stays ensemble-candidate, now re-scoped onto the new
  best (fork proposals were validated on gate-7 links).
- Next: EXP-0019 gate-10 + r10-fork combination (must beat the NEW best on
  both folds with div gain, else the combination is parked and r10 remains
  a standalone ensemble-candidate).
