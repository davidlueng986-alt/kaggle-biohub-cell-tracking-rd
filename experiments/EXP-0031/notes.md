# Notes — EXP-0031 Image-side fork proposals

## Log
- 2026-09-10: `bash experiments/EXP-0031/run.sh` -> exit 0, gate FAIL recorded (STOP).
- Reference A recompute matches frozen values exactly: rec 0.9820, raw 0.9533,
  adj 0.9804, ec 143/2/5, dc 0/0/0 (div 1.0-empty) — pipeline faithful.
- Fork r10 on detected graphs: raw 0.9286 (d -0.0248), adj 0.9549 (d -0.0255),
  ec 143/6/5 (edge FP +4, TP/FN unchanged), dc 0/3/0 (div FP 3, div_j 1.0 -> 0.0),
  n_fork_extra 6. Recall unchanged (0.9820, same nodes).
- Gate: edge_ge_A false, div_FP_zero false, recall_ge_A_minus_005 true -> STOP.

## Decisions
- STOP: image forks PARKED alongside oracle r10 standalone. The prior held up
  exactly as feared: on detected graphs the extra (unannotated/false) nodes give
  the proposer unmatched targets within 10um, so proposals become FPs — 6 extra
  edges, 4 counted edge FPs + 3 evaluable division FPs, with zero possible TP
  (0 GT divisions in window). Per the division sub-gate any FP kills it.
- Mechanism: TP/FN identical (143/5) — proposals only ADD edges; on oracle graphs
  the added edges hit true daughters (EXP-0005: div 3/0/1, zero edge cost), while
  on image graphs they attach to nearby clutter. Geometry-only proposals cannot
  distinguish daughters from false detections; needs appearance/motion gating
  (H-003) before any image-side retry.
- Division-active full-video context (EXP-0005 r10, oracle graphs, for the record):
  fold0 44b6 score unchanged (d_edge 0.0), fold1 6bba +0.00112 edge, div 3/0/1
  (div_j 0.75), gate true both folds. The oracle r10 result stands; this experiment
  only closes the image-side door for the standalone proposer.
- Next: NO EXP-0034 (full-video image-fork test not recommended after STOP).
  Candidates that could reopen: H-003 appearance-gated proposals, or isolation-veto
  variants — each behind its own fresh window gate.
