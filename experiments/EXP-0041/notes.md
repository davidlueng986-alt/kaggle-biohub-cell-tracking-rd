# Notes — EXP-0041 Window-best full-video validation 98.5/97.5

## Log

- Created via scripts/new_experiment.sh (EXP-0041 confirmed free).
- Probe: single-frame @98.5 detect on 0b24845f t25 → 153 dets, 0.62 s compute
  (~1.1 s wall incl. startup) → ~200 frames fits < 35 min budget.
- Window refs verified by reading EXP-0024/metrics.json: 0b24845f@98.5
  recall 0.80 (8/10, det/f 155.0); 0c582fdc@97.5 recall 0.50 (5/10,
  det/f 184.2). Bars for the adj criterion = fresh CLI rescores of frozen
  EXP-0040 @96.0 preds (read-only, never pasted); values recorded in
  metrics.json after rescoring.
- IMPORTANT context found (read-only): EXP-0034 already ran full-video at
  these exact window-best levels (0b24845f@98.5 full rec 0.4314 / adj 0.2249;
  0c582fdc@97.5 full rec 0.4930 / adj 0.2767) with the identical frozen DoG
  settings, and judged transfer vs its window-slice edge bar (BREAKS/HOLDS
  → STOP on 2/3 incl. 6bba). This mission's verdict rule differs (recall vs
  window recall AND adj vs best full-video adj so far), so this rung is
  executed as specified regardless; comparison with EXP-0034 recorded below
  as a determinism/cross-check, not as the verdict bar.
- Ran `bash experiments/EXP-0041/run.sh` → exit 0, ~7 min wall (200 frames
  @ ~0.65 s/f + link/score). Determinism cross-check: total_det 16493/16531,
  edge adj 0.2249/0.2767 with ec 12/7/37 and 21/9/49 reproduce EXP-0034
  bit-exact; micro recalls 22/51=0.4314 and 35/71=0.4930 also exact.
  Bar rescores of frozen EXP-0040 @96 preds match the ledger bit-exact
  (rescore_match_ledger=true both samples: adj 0.1872/0.1874, raw
  0.1818/0.1795).

## Decisions

- Scoring via trusted score.py CLI verbatim (scripts/* untouched); no scipy
  solver swap — EXP-0034 proved CLI scoring tractable for these samples.
- Recall diagnostic (micro over GT-annotated frames) via scipy LSA in the
  assembly step only; not part of the trusted score.
- No scripts/*, docs/*, knowledge/*, other-experiment, or data writes; no pip;
  no kaggle; no commits. All new files under experiments/EXP-0041/ only.

## Results (PROTOCOL v1.1, scorer v1.1.0)

- 44b6_0b24845f @98.5: full recall (macro) 0.4875 vs window 0.8000
  (d=-0.3125, need ≥-0.10 → FAIL); adj 0.2249 vs rescored @96 bar 0.1872
  (d=+0.0377 → PASS). => BREAKS (recall collapse; window's 10 GT nodes
  overstated recall vs full 51 GT nodes, t11-50). Micro recall 0.4314 —
  verdict invariant to macro/micro.
- 44b6_0c582fdc @97.5: full recall 0.4930 vs window 0.5000 (d=-0.0070 → PASS);
  adj 0.2767 vs rescored @96 bar 0.1874 (d=+0.0893 → PASS). => HOLDS
  (transfers almost exactly; also beats the @96 bar on adj).
- Overall: 1/2 HOLDS => STOP. Window-best levels do NOT transfer reliably
  (sample-dependent: holds on 0c582fdc, breaks on 0b24845f). No per-sample
  policy promotion; no further rung from this agent.
