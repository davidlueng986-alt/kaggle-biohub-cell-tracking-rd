# Notes — EXP-0044 Image r10 forks on 6bba_05db0fb1 full video (3 GT divisions)

## Log

- Scaffolded via scripts/new_experiment.sh EXP-0044 (verified next-free:
  ls showed EXP-0043 taken by a concurrent agent; EXP-0044 free).
- Det-source correction: mission cited
  EXP-0009/full_6bba_05db0fb1_t<0-99>.json, but EXP-0009 contains only
  44b6_0113de3b + 6bba_05b6850b per-frame dets. Used the @98.5 per-frame
  dets in EXP-0021 (same pct threshold; frozen, byte-reused, no
  re-detection). GT from experiments/EXP-0003/gt/6bba_05db0fb1_gt.json.
- Ran run.sh end-to-end, exit 0. Base arm exactly reproduces the EXP-0021
  reference row (raw 0.19686, adj 0.20917, ec 251/92/932, div 0/0/3;
  recall recomputed 0.290299 = EXP-0021's 0.2903) — reuse verified.
- Nothing outside experiments/EXP-0044/ written; no scripts/docs/knowledge
  edits; no pip installs; no kaggle calls; no git commits.

## Decisions

- Plain r10 (isolation=False, base_maxd default 7.0) per mission spec; no
  gate widening (EXP-0017 arm2 rejection stands).
- Verdict logic encoded in run.sh step 3/3 per mission GO/MIXED/STOP rules.

## Results

- Nodes 26168 (T_pred) vs T_true 69800; base edges 21665; fork adds
  n_fork_extra=2393 → 24058 edges.
- Base: raw 0.19686, adj 0.20917, ec TP/FP/FN 251/92/932, div 0/0/3.
- Fork r10: raw 0.19545, adj 0.20767, ec 258/137/925, div 0/35/3.
- Deltas: d_adj −0.00150, d_raw −0.00141, d_div_TP 0, d_div_FP +35,
  d_score −0.00150.
- Interpretation: on the dense image graph (@98.5 over-detects ~262
  nodes/frame vs ~12 GT-annotated nodes/frame matched), the 10 um proposal
  radius fires 2393 times; edge TP +7 is swamped by edge FP +45, and every
  proposed fork that lands near annotated lineage counts as a division FP
  (35) with zero TPs — the scorer's sparse-aware guards do not save
  geometry-only proposals here. The oracle-r10 pattern does NOT translate
  to image. Verdict: STOP — image forks stay parked.
