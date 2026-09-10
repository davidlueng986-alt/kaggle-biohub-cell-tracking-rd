# EXP-0031 — Image-side fork proposals

## Hypothesis
The r10 fork proposer (`fork_link.link`, propose_um=10.0 on the gate-7 base),
validated on ORACLE graphs (EXP-0005: div 3/0/1 at zero edge cost; EXP-0006
replication; EXP-0019 combo), is harmless on DETECTED (image) graphs: on the
frozen 6bba_05b6850b window (t20-29 + t40-49, 0 GT divisions) it keeps edge
raw+adj >= reference A with div FP == 0 and recall >= A - 0.005.

## Background
- docs/PROTOCOL.md v1.1 (frozen metric: adjusted_edge_jaccard + 0.1*division_jaccard;
  division sub-gate: fork-count increases need division gain AND no edge regression).
- knowledge/STATE.md: oracle r10 standalone validated; never tested on detected graphs
  where extra nodes may turn proposals into FPs.
- Reference A (EXP-0013 window @98.5): rec 0.982, raw 0.9533, adj 0.9804, ec 143/2/5,
  div 1.0-empty. Base gate stays 7 (EXP-0017 arm2 rejected gate-10 widening image-side).

## Falsification criteria
Window-only gate (div TP>0 impossible — 0 GT divs in window, so this is a pure
harmlessness/discipline test): PASS requires edge raw AND adj >= A recompute,
AND div FP == 0, AND recall >= A - 0.005. Any division FP kills it per the
sub-gate. FAIL -> STOP: image forks parked alongside oracle r10 standalone
(no full-video image-fork test).
