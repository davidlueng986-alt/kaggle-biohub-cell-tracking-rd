# EXP-0050 — Gate-7 vs gate-10 linker gate test, all 6 IMAGE graphs

## Hypothesis
Linker gate maxd=7.0 beats maxd=10.0 on adjusted edge Jaccard for 6/6 full-video
IMAGE graphs (frozen DoG detections, PROTOCOL v1.1 scorer gate fixed at 7um).

## Background
- Prior probe: gate-7 beats gate-10 on 4 visible samples
  (+0.28/+0.002/+0.006/+0.017 adj); 05db0fb1/062c8d37-class density untested at
  gate-10 — tested fresh here on all 6.
- Oracle arm prefers gate-10 (EXP-0018 PROMOTED); this rung is IMAGE graphs only.
- Linker: `baseline_link.link` (causal t->t+1 Hungarian, <=1 outgoing/node, zero
  forks expected); scorer: scripts/score.py v1.1.0.

## Falsification criteria
Any sample with adj(gate10) > adj(gate7) rejects the 6/6 claim -> verdict MIXED
(record sample, magnitude, mechanism hypothesis). 6/6 gate7 wins -> CONFIRM.

## Result
MIXED: 2 flips (see metrics.json). 6/6 claim REJECTED.
