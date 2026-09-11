# Plan — EXP-0050 Gate-7 vs gate-10 linker gate test, all 6 IMAGE graphs

## Config / seeds
- Deterministic, CPU-only. No seeds (Hungarian exact; scipy C path N>60, same optimum).
- Frozen det sources: 44b6_0113de3b@99.0 <- EXP-0008; 6bba_05b6850b@98.5 <- EXP-0009;
  44b6_0b24845f@99.0, 44b6_0c582fdc@99.0, 6bba_05db0fb1@98.5, 6bba_062c8d37@98.5 <- EXP-0021.
- Det ids restart per frame -> reassigned globally unique gid per video.
- Node fields id/t/z/y/x only (matches EXP-0021 reference behavior).
- GT: experiments/EXP-0003/gt/<sid>_gt.json (true T_true). Scorer gate fixed 7um.

## Steps
1. `bash experiments/EXP-0050/run.sh` — assemble 6 videos, link maxd=7.0 + maxd=10.0,
   score both vs full GT, write metrics.json (+ per-gate pred JSONs).
2. Verdict rule: gate7 >= gate10 adj on 6/6 -> CONFIRM, else MIXED with flips.
3. Record per-sample raw/adj/div, TP/FP/FN, div counts for both gates in metrics.json.

## NOTE
EXP-0047 was specified but taken by a parallel experiment; EXP-0049 likewise
claimed mid-run. Used next-free EXP-0050 (noted per mission instructions).
