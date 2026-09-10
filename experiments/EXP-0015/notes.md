# Notes — EXP-0015 Appearance probe (H-003)

## Log
- 2026-09-09: `bash experiments/EXP-0015/run.sh` → exit 0, 1/2 checks.
- NCC by scorer class, frozen 6bba@98.5 graph (4229 edges, ~10 min cached):
  TP (n=699): mean 0.865, p25/50/75 0.913/0.954/0.973.
  FP (n=30): mean 0.642, p25/50/75 0.461/0.710/0.916.
  ignored (n=3500): mean 0.862 ≈ TP — sanity: unannotated-region links are
  overwhelmingly correct-looking (sparse GT, not bad tracking).
- Margin 0.223 ≥ 0.15 ✓ but quartile bar missed by 0.003 (FP p75 0.916 vs
  TP p25 0.913) ✗. FP distribution is bimodal in effect: half clearly wrong
  (NCC < 0.71), half photometrically identical to TPs (leftover confusion
  between similar-looking cells — geometry-identical twins).

## Decisions
- `keep-trying` — falsified AS WRITTEN (strict quartile bar), refined:
  **hard NCC veto PARKED** (would eat TP tail), **soft appearance weight GO**
  (EXP-0016): add λ·(1−NCC) into assignment cost with explicit TP-cost
  budget, gated on window edge — margin 0.22 funds FP reduction that a veto
  cannot buy. The twins (high-NCC FPs) remain unfixable classically;
  recorded as the residual for learned features.
