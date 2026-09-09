# Notes — EXP-0006 Replication rung for r10 (H-002+H-003)

## Log
- 2026-09-09: `bash experiments/EXP-0006/run.sh` → exit 0. Perturbation seeds
  {0,1,2} (σ=0.3 vox jitter on pred-side positions, scored vs clean GT) +
  noise-matched base arm (same jittered inputs through `baseline_link.py`) +
  corrected LOO (same-subset head-to-head; an earlier draft compared LOO
  micros against full-set floor micros — mechanically wrong, fixed before
  verdict: dropping a high sample lowers any micro).
- Literal criteria (as written in hypothesis): FAILED — seed0 div sums
  (2,0,2) vs unperturbed (3,0,1); edge wobble to ±0.0048 vs the ±0.002 band.
- Refined analysis (added mid-run, documented in run.sh): the wobble belongs
  to the BASE linker (noise-matched base moves identically); variant−base on
  identical inputs is ≥ +0.0000 edge and ≥ +0.00 div on all 18 runs; FP=0 in
  all 18 runs; LOO same-set passes 6/6. The flickering TP is the 9.08 µm
  boundary pair vs the 10 µm radius — a knife-edge, not noise in the method.
- 44b6 side byte-identical across seeds (sparse graphs, unambiguous links).

## Decisions
- `keep-trying` — r10 KEEPS ensemble-candidate status (asymmetric bet
  replicates: zero cost in 18/18, gain in 17/18 sample-runs). No promotion
  (no fold0 win possible + deterministic single-config).
- Boundary fragility (9.08 µm pair) is now the top H-003 argument: appearance
  evidence would not flicker under sub-voxel jitter. Next: H-002 image-based
  detection (DoG probe on real zarr timepoints) to beat floor on merit, and/or
  H-003 appearance-gated fork confirmation.
