# Notes — EXP-0029 Truncate gate + kernel v6 (H-005)

## Log
- 2026-09-10: truncate probe (t25): identical sets at 4.0/3.0/2.0 (45
  nodes, 8/8), gauss 0.36→0.24 s. Window verdict (20 frames): 20/20 frames
  DIFFER, recall 0.970 vs 0.982, raw 0.9145 vs 0.9533 (139/4/9 vs 143/2/5).
  Single-frame probes do not transfer across density — same lesson as
  EXP-0011's window gate, one level up. REJECTED (artifacts matter);
  default stays 4.0, `--truncate` kept as CLI-validated option.
- Kernel upgrade (vectorized centroids port, verified identical locally on
  frozen A_t25): v6 COMPLETE, 112,599 rows IDENTICAL count, **0.11 h vs
  v5's 0.36 h (3.3×)** — Kaggle CPUs penalize the argwhere loop more than
  this VM, so the payoff beat local projections. Hidden projection reframes
  ~18 h → ~5.5 h: inside 12 h with ~2× headroom (density-mix dependent).
- Submitted v6 as ref 56147475 (PM rule: materially-faster kernel + slots
  ≥1 both held; slots now 0 — no more submits today regardless). v5 ×3
  hidden reruns still queued (may time out; v6 supersedes on timing).

## Decisions
- `keep-trying` — truncate REJECTED, vectorized ADOPTED everywhere (repo +
  kernel). H-005: detection no longer the hard blocker (linking was never
  it — EXP-0025; remaining risk is dense-hidden mix, measurable only via LB).
- Next: read LB diagnostic on arrival (transfer verdict on fallback levels
  is the top unknown); else EXP-0030 learned-detector scoping (GPU).
