# EXP-0046 — orphan-driven second-edge pass validation

## Hypothesis
An orphan-driven second-edge pass (add u->w iff: base edge u->v exists,
w at t(v), w != v, dist(w,v) <= 10um, w has NO incoming edge, u has exactly
1 outgoing edge; nearest w only, one extra per source) recovers the
EXP-0045 LOST-AT-LINKING division (6bba_062c8d37 parent 90001276 ->
daughters 91001298/91001299, all detected <= 1.73um, daughter 4598 left
orphan by the 1-to-1 linker) with ZERO division FPs and no edge regression,
while adding zero forks on the 6bba_05db0fb1 control (its 3 divisions are
detection-lost, so no orphan-gated fork should fire there).

## Background
- docs/PROTOCOL.md v1.1 (score = adjusted_edge_jaccard + 0.1*division_jaccard;
  division sub-gate: fork-count increases need division gain AND no edge regression).
- experiments/EXP-0045/notes.md + metrics.json (division-evidence audit).
- experiments/EXP-0044 (r10 radius-rule: 35 FPs / 0 TPs — fires on clutter, not orphans).

## Falsification criteria (pre-registered bar)
- Main (6bba_062c8d37): div TP >= 1 AND div FP == 0 AND edge adj >= base.
- Control (6bba_05db0fb1): zero new forks.
- Pass both -> GO (recommend EXP-0047 replication, do not run).
  Fail either -> STOP (orphan rule parked with r10).
