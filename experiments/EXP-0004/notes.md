# Notes — EXP-0004 Fork-proposing linker variant (division sub-gate)

## Log
- 2026-09-09: scaffolded via `new_experiment.sh`; `bash experiments/EXP-0004/run.sh` → exit 0.
- Variant: base oracle Hungarian + ≤1 extra edge/source to unmatched target
  within 15 µm proposal radius (`scripts/fork_link.py --propose-um 15.0`).
  Key measurement driving design: GT daughter pairs sit 8.5–12.5 µm apart
  (beyond the 7 µm matching gate), so radius-7 proposed zero forks.
- Result vs EXP-0003 floor:
  - fold0 44b6: micro 1.0933 → 1.0933 (+0.0000, no change — zero GT divs, zero proposals). Stability ✓.
  - fold1 6bba: micro 1.0705 → 1.0680 (−0.0025). Regression ✗.
  - Division sums: floor 0/0/4 → variant 3/10/1 (gain ✓, 3 of 4 GT divisions recovered).
  - Per-sample: 05db0fb1 div 0→0.18 (TP2, FP8), 062c8d37 div 0→0.5 (TP1, FP1),
    05b6850b div 1.0→0.0 (spurious fork, FP1 on a 0-division sample).
- Verdict: sub-gate REJECT for promotion (edge regression on fold1), recorded
  in `metrics.json` (`sub_gate.pass: false`). Single-seed run caps at
  keep-trying regardless (§4 gate 1).

## Decisions
- `keep-trying` — signal kept, noise must go: radius-15 recovers real mitoses
  but 10 FPs cost more edge than 3 TPs buy. Next EXP-0005: tighter gating —
  candidates: (a) smaller radius ablation (10/12 µm), (b) require the extra
  target's nearest GT-component to match the source branch (cross-component
  veto already in scorer — use it as a proposal filter), (c) H-003 appearance
  check on the daughter pair. Do NOT widen radius.
