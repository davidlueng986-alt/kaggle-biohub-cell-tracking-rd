# Notes — EXP-0030 Min-size ablation

## Log

- `bash experiments/EXP-0030/run.sh` → exit 0, gate FAIL recorded.
- Window (t20–29 + t40–49 @98.5, GT subgraph: 167 nodes / 148 edges, T~1272):
  - ms50 (=A, recomputed): rec 0.9820, det 911, raw 0.9533 / adj 0.9804
    (143/2/5) — reproduces EXP-0013 A exactly (rec 0.982, raw 0.9533,
    adj 0.9804, ec 143/2/5).
  - ms25: rec 0.9820 (Δ 0.0), det 952 (+41), raw 0.9533 (Δ 0.0),
    adj 0.9773 (Δ −0.0031), ec 143/2/5 — 41 extra detections buy ZERO
    GT matches; adj drops via the T_pred over-prediction penalty.
  - ms100: rec 0.9760 (Δ −0.0060, −1 GT match), det 872 (−39),
    raw 0.9533 (Δ 0.0), adj 0.9833 (Δ +0.0029), ec 143/2/5 — fewer dets
    lift adj via smaller T_pred, but lose a real cell.
- Mechanism: raw edge + ec identical (143/2/5) across all three — the
  detections gained/lost by moving the size floor sit outside GT-annotated
  structure, so the sparse-aware FP rule ignores them; only recall (real
  cells near the floor) and adj (T_pred penalty) move. The window misses
  are NOT small-floor recoverable (ms25 adds nothing matched), and the
  floor at 100 already eats one real GT cell.

## Decisions

- STOP — gate FAIL: neither ms25 nor ms100 matches-or-beats ms50(A) on
  all of recall/raw/adj (ms25 fails adj; ms100 fails recall). min-size
  stays 50. No full-video commit; EXP-0033 NOT requested.
- Standing policy unchanged: 44b6@99.0 + 6bba@98.5/min-size-50 base.
