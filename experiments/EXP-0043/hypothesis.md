# EXP-0043 — 062c8d37 full-video @96.0 replication of EXP-0039

## Hypothesis

@96.0 percentile is a general dense-tissue operating level, not sample luck:
on held-out dense-ish sample 6bba_062c8d37, full-video @96.0 detection +
baseline_link (gate 7 um) matches or beats the @98.5 bar on BOTH recall
(>= 0.90) AND adjusted edge jaccard (>= @98.5 bar 0.8647).

## Background

- docs/PROTOCOL.md v1.1 (score = adjusted_edge_jaccard + 0.1*division_jaccard).
- knowledge/STATE.md: EXP-0039 GO — 05db0fb1 full-video @96.0 recall
  0.29->0.68, adj 0.209->0.482 (single-sample evidence).
- EXP-0021 row: 062c8d37 @98.5 full-video recall 0.930, raw 0.8508,
  adj 0.8647 (recomputed-by-rescoring here, never pasted).

## Falsification criteria

- REPLICATES: recall >= 0.90 AND adj >= @98.5 bar (0.8647)
  -> @96-as-dense-policy GO.
- MIXED: exactly one holds -> STOP (sample luck; @96 not general).
- DIVERGES: neither holds -> STOP (sample luck).
