# HYPOTHESES backlog

Status values: `backlog` | `active` | `done` | `rejected`.

| ID    | Title                              | Rationale / prediction                                              | Status  | Linked exps |
|-------|------------------------------------|---------------------------------------------------------------------|---------|-------------|
| H-001 | Embryo-CV baseline                 | With only 2 train embryos, embryo-grouped CV is the only honest scorer; frame-split CV will overfit. Predict: embryo-CV baseline < frame-split score but transfers to LB. | active | EXP-0000 (template), EXP-0001 (done, harness keep-trying), EXP-0002 (done, geometric validation keep-trying) |
| H-002 | DoG + Hungarian + ILP linker       | Classical detect (DoG) + Hungarian frame matching + ILP gap-closing beats greedy linking on edge Jaccard by cutting ID switches. Oracle-linker floor set by EXP-0003 (worst-fold edge 1.0705, div 0/0/4); image-based detection still open. | active | EXP-0003 (done, oracle floor keep-trying) |
| H-003 | Division gating                    | Explicit mitosis classifier / appearance gating lifts the 0.1-weighted division_jaccard without hurting edge Jaccard. Geometry-only precursor tested in EXP-0004 (radius-15: 3/4 TPs but 10 FPs → sub-gate reject); appearance/tighter gating still open → EXP-0005. | active | EXP-0004 (done, sub-gate reject keep-trying) |
| H-004 | T_true penalty calibration         | Voxel scale pinned 2026-09-09 (z=1.625/y=x=0.40625) + `T_true`=`estimated_number_of_nodes` (Evaluation/Data tabs + sample CSV). Predict: pinning scaling + `T_true` vs train-embryo counts changes absolute score and promotion margins. Validated mechanically in EXP-0002 (inflation 1.0→0.9); real-data calibration still open. | active | EXP-0002 (done, mechanical validation) |
| H-005 | ILP timing budget                  | Global ILP over 100×64×256×256 videos may blow the ~80–96 s/video (12 h) budget; per-video latency must be profiled early. Predict: full-video ILP exceeds budget → needs windowed/slimmed fallback path. | backlog | — |

## Notes

- New hypotheses append rows; never rewrite history — status transitions only.
- Every experiment folder links one hypothesis id (`experiments/EXP-XXXX/hypothesis.md`).
- Promotion rule (see README.md): local embryo-CV gain + cross-fold stability required.
- H-001 activated 2026-09-09 (EXP-0001, dryrun-experimenter). H-004 derived from PROTOCOL §1 TODO (µm scaling / `T_true` provenance). H-005 derived from PROTOCOL §6–7 (12 h budget, per-video profiling).
- 2026-09-09: H-004 activated (EXP-0002 mechanical validation); voxel + T_true pins verified from Evaluation/Data tabs + sample_submission.csv. H-001 stays active (real embryo-CV transfer untested → EXP-0003).
- 2026-09-09 (GOLD): subset 6 downloaded (738/738); H-002 activated (EXP-0003 oracle floor); EDA confirms embryo grouping, sparse GT, voxel pins — COMPETITION.md unchanged.
- 2026-09-09 (GOLD): EXP-0004 sub-gate reject (H-002+H-003); H-003 activated. GT daughter separation 8.5–12.5 µm measured → radius-7 proposes nothing, radius-15 recovers 3/4 with 10 FPs. EXP-0005 tighter gating next.
- 2026-09-09 (GOLD): EXP-0005 selects r10 (plateau r10==r11, FP=0, div 3/0/1; r9 under-recovers, r≥12 degrades; isolation no-op ≤12). r10 = ensemble-candidate, keep-trying (no fold0 win possible + single-run ceiling → EXP-0006 replication).
