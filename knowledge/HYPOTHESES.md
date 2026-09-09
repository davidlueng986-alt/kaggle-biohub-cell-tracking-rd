# HYPOTHESES backlog

Status values: `backlog` | `active` | `done` | `rejected`.

| ID    | Title                              | Rationale / prediction                                              | Status  | Linked exps |
|-------|------------------------------------|---------------------------------------------------------------------|---------|-------------|
| H-001 | Embryo-CV baseline                 | With only 2 train embryos, embryo-grouped CV is the only honest scorer; frame-split CV will overfit. Predict: embryo-CV baseline < frame-split score but transfers to LB. | active | EXP-0000 (template), EXP-0001 (in progress, owner: dryrun-experimenter) |
| H-002 | DoG + Hungarian + ILP linker       | Classical detect (DoG) + Hungarian frame matching + ILP gap-closing beats greedy linking on edge Jaccard by cutting ID switches. | backlog | — |
| H-003 | Division gating                    | Explicit mitosis classifier / appearance gating lifts the 0.1-weighted division_jaccard without hurting edge Jaccard. | backlog | — |
| H-004 | T_true penalty calibration         | `T_true` coarse-count source/provenance is unverified (PROTOCOL §1 TODO); miscalibrated `T_true` or voxel→µm scaling silently shifts adjusted_edge_jaccard. Predict: pinning scaling + `T_true` vs train-embryo counts changes absolute score and promotion margins. | backlog | — |
| H-005 | ILP timing budget                  | Global ILP over 100×64×256×256 videos may blow the ~80–96 s/video (12 h) budget; per-video latency must be profiled early. Predict: full-video ILP exceeds budget → needs windowed/slimmed fallback path. | backlog | — |

## Notes

- New hypotheses append rows; never rewrite history — status transitions only.
- Every experiment folder links one hypothesis id (`experiments/EXP-XXXX/hypothesis.md`).
- Promotion rule (see README.md): local embryo-CV gain + cross-fold stability required.
- H-001 activated 2026-09-09 (EXP-0001, dryrun-experimenter). H-004 derived from PROTOCOL §1 TODO (µm scaling / `T_true` provenance). H-005 derived from PROTOCOL §6–7 (12 h budget, per-video profiling).
