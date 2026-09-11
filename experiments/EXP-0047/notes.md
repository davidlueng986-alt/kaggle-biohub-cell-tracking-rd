# Notes — EXP-0047 gate-10 vs gate-7 on dark image graphs

## Log
- Linking-only re-score of frozen EXP-0021 detections (maxd 7.0 vs 10.0), 5 samples.
- g7 reproduces EXP-0021 numbers exactly (sanity: 05b6850b adj 0.8194).

## Decisions
- HOLD-g7 (3/5): 0b24845f −0.002, 05db0fb1 −0.017, 05b6850b −0.006.
- Nuance: gate-10 WINS on 0c582fdc (+0.026, sparse-dark) and 062c8d37 (+0.013, clean-dense).
  Gate is sample-conditional, not universal — supports v7 gate-7 as the safe default
  (never catastrophically wrong) while hidden-embryo regime is unknown.
- Overlap note: concurrent session scaffolded EXP-0050 (same gate question, all 6).
  This EXP-0047 stands alone (done first, 5 samples); cross-check 0050 on arrival, do not rerun.
