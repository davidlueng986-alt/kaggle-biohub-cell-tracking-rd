# Notes — EXP-0040 Replicate @96 dark-sample recall gain on 0b24845f + 0c582fdc full-video

## Log

- Created via scripts/new_experiment.sh (EXP-0040 confirmed free).
- Probe: single-frame @96 detect on 0b24845f t50 -> 216 dets, 0.68 s compute
  (~1.2 s wall incl. startup) => ~200 frames fits < 35 min budget.
- Wrote score_fast.py (EXP-dir-local, EXP-0039 pattern): runtime-only scipy
  solver swap for score._hungarian + equivalence gate; scripts/* untouched.
- Ran run.sh 1/4 (detect 2x100 @96.0) + 2/4 (global re-id + BL.link defaults)
  + 3/4 (score_fast.py: @96 trusted score + fresh rescore of frozen EXP-0021
  @99 preds) OK. Equivalence gate passed on real frames (both samples,
  t=0/20/50/99, both pct arms); scores.json written (wall 5.2 s scoring).
- Assembly 4/4 first failed: KeyError 'edge' (bar dict key is 'edge_adj';
  3 occurrences in run.sh). Fixed run.sh (lines ~74-75, verdict_reason) and
  re-ran ONLY the fixed step-4 block manually — identical code to fixed
  run.sh, so cold rerun reproduces metrics.json (detect/link/score artifacts
  already on disk and deterministic).
- Rescore check: fresh @99 rescores match EXP-0021 ledger exactly
  (rescore_match_ledger=true both samples; raw/edge/div/ec/dc identical).

## Decisions

- Bars = recomputed-by-rescoring (never pasted): rescore values used for adj
  comparisons; ledger recall used for the +0.10 recall-gain criterion
  (rescorer does not recompute recall; ledger recall is the frozen reference).
- No scripts/*, docs/*, knowledge/*, other-experiment, or data writes; no pip;
  no kaggle; no commits. All new files under experiments/EXP-0040/ only.

## Results (PROTOCOL v1.1, scorer v1.1.0)

- 44b6_0b24845f: @96 recall 0.4000 / raw 0.1818 / adj 0.1872 (ec 10/6/39,
  dc 0/0/0, div 1.0) vs @99 bar recall 0.3250 / raw 0.0980 / adj 0.1040
  (ec 5/2/44). d_rec=+0.0750 (< +0.10 FAIL), d_adj=+0.0833 (PASS).
  => DIVERGES (criterion shortfall, NOT a reversal: both recall and adj
  improve, but recall gain misses the bar).
  Mechanism: T_ratio 0.7016 vs 0.3962; det/f 230.09 vs 129.92 — extra
  detections convert to +5 edge TP at cost of +4 edge FP; GT tiny
  (51 nodes / 49 edges), so recall moves slowly per detection.
- 44b6_0c582fdc: @96 recall 0.4085 / raw 0.1795 / adj 0.1874 (ec 14/8/56)
  vs @99 bar recall 0.1972 / raw 0.0909 / adj 0.0958 (ec 7/7/63).
  d_rec=+0.2113 (PASS), d_adj=+0.0915 (PASS). => REPLICATES.
  Mechanism: T_ratio 0.5595 vs 0.4571; det/f 156.42 vs 127.79 — +7 edge TP,
  +1 edge FP net; count cost stays below parity so adjustment bonus holds.
- Overall: 1/2 REPLICATES => MIXED (sample-specific: replicates on
  0c582fdc, diverges on 0b24845f by recall-gain shortfall).
- Policy: per mission, MIXED => sample-specific note, no EXP-0041
  recommendation; @96 generalizes beyond 05db0fb1 on 1 of 2 dark samples.
