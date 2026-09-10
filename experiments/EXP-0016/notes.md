# Notes — EXP-0016 Soft appearance weight (H-003)

## Log
- 2026-09-09: `bash experiments/EXP-0016/run.sh` → exit 0. Plus post-hoc
  null confirmation (W=8/16/32, same harness).
- Anchor PASSED: W=0 reproduces EXP-0013 A bit-exactly (143/2/5).
- W=1/2/4: byte-identical to W=0 (781 NCCs computed, zero flips, tpcost 0).
  W=8/16/32: STILL identical — even penalties dwarfing the 7 µm gate flip
  nothing. Mechanism: among gated competitors NCC ≈ 0.9–0.98 for ALL pairs
  (shared bright tissue at (9,21,21)-patch scale), so cost ordering ==
  distance ordering. The margin-0.22 class signal (EXP-0015) lives in
  label-conditionals, not in live candidate margins — unspendable here.
- Debug incident (kept for the record): first run scored 37/601/136 —
  detection JSONs restart ids per frame and the driver linked collided
  identities. Fixed with global re-id; anchor then passed. Lesson: id
  namespaces are guilty until proven innocent (applies to notebook path).
- GO-by-equality was mechanically True but overruled: a treatment that
  provably cannot change the outcome must not consume a full-video rung.

## Decisions
- `keep-trying` — **H-003 classical PARKED** (probe signal real,
  unspendable in assignment). Residual: high-NCC FP twins + dim cells →
  learned detector/features (GPU-notebook territory) or motion evidence.
- Ladder status: detection branch parked (thresholds/splits/scales),
  linker geometry rung complete (r10 ensemble-candidate), appearance
  parked. Remaining cheap CPU rung: gap-closing/ILP-lite for the 55 oracle
  FNs (H-002/H-005) + submit-path timing. Next: EXP-0017 gap-closing probe.
