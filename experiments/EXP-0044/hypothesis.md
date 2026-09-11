# EXP-0044 — Image r10 forks on 6bba_05db0fb1 full video (3 GT divisions)

## Hypothesis

The oracle-r10 fork pattern translates to the image graph: running
`fork_link.link(nodes, propose_um=10.0)` on the gate-7 base links over the
frozen @98.5 full-video detections of 6bba_05db0fb1 — the first image graph
whose GT contains divisions (3) — recovers ≥1 division TP with 0 division
FPs and no edge-adjusted regression vs the no-fork base (GO gate).

## Background

- PROTOCOL v1.1: score = adjusted_edge_jaccard + 0.1*division_jaccard;
  scorer scripts/score.py v1.1.0. Division sub-gate: fork-count increases
  need division gain AND no edge regression.
- Prior image-fork tests ran on 0-division windows/samples (EXP-0031:
  div-FP 3, parked). This is the first image test where division TPs exist.
- Fork proposer scripts/fork_link.py `link(gt, propose_um, isolation,
  base_maxd)`; r10 = propose_um 10.0 on gate-7 base (base_maxd default 7.0;
  no widening per EXP-0017 arm2).
- Det source note: mission text cited EXP-0009 per-frame dets, but EXP-0009
  only holds 44b6_0113de3b + 6bba_05b6850b. The 6bba_05db0fb1 @98.5
  per-frame dets live in EXP-0021 (same pct, frozen, byte-reused here).
- Reference bar (EXP-0021 row, recomputed — never pasted): recall 0.2903,
  raw 0.1969, adj 0.2092, ec 251/92/932, div 0/0/3.

## Falsification criteria

- GO: div TP ≥ 1 with div FP == 0 AND edge adj ≥ base.
- MIXED: div gain with small edge cost (quantify both).
- STOP: div FP > 0 without TP gain, or edge adj regresses > 0.01.
- Outcome: STOP (div 0/35/3, d_adj −0.0015 — div FPs with zero TP gain).
  Image forks stay parked.
