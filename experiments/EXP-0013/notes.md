# Notes — EXP-0013 Window gate (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0013/run.sh` → exit 0, gate FAIL recorded.
- Window (t20–29 + t40–49, GT-dense: 167 nodes / 148 edges, T~1272):
  - A @98.5 base: rec 0.982, raw 0.9533 / adj 0.9804 (143/2/5) — strong.
  - B @98.0+split: rec 1.000, raw 0.7356 (128/**26**/20) — recall up, edge collapses.
  - C +prom0.7: rec 0.994, raw 0.7457 (129/25/19) — 111→74 splits, edge still far below A.
  - D +phased: **identical to C** (129/25/19; phased path asserted engaged).
- Mechanism (diagnosed): phased==C means NO stealing occurs — primaries'
  links are untouched by fragments. The FPs are leftover-to-leftover
  confusion: fragment nodes near GT tracks link to annotated-but-wrong
  targets that single-Hungarian also leaves unmatched. No linking
  discipline without appearance/motion evidence fixes that; FEWER, better
  detections win (A detects 911 vs D's 1141 on the window).
- Prominence helped modestly (FP 26→25, splits −33%) but nowhere near
  enough to change the verdict.

## Decisions
- `keep-trying` — gate FAIL → STOP: splitter family PARKED for linking
  purposes (detection-side recall value stands, but unusable until links
  stop confusing). Standing policy unchanged: 44b6@99.0 + 6bba@98.5 base
  (worst adj 0.8194).
- Next: dim-cell scale terms (smaller-σ DoG pass for small dim cells, fused
  carefully) or H-003 appearance-gated linking (EXP-0014). Window gates
  keep the edge readout (lesson holding for the third rung).
