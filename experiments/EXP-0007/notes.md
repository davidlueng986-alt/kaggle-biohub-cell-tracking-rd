# Notes — EXP-0007 DoG detection probe (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0007/run.sh` → exit 0, checks pass.
- Detection (DoG σ=(1,3,3)/(1.6,5,5), components ≥50 vox, CPU):
  - pct 99.0: recall **1.00 both samples** (44b6: 430 det/3 frames; 6bba: 144 det/3 frames).
  - pct 99.5: recall 0.00 / 0.44 — operating point confirmed at 99.0 (annotated
    cells are bright-but-not-brightest; raising threshold deletes them first).
  - Match-rate (detections hitting GT) 0.01–0.12 — EXPECTED, not failure: GT
    is sparse, the extras are overwhelmingly real unannotated cells.
- Mini-graph end-to-end (detected t0–t2 + Hungarian links vs GT subgraphs):
  - 44b6@p99.0: edge_raw 1.0000 / adj 1.0444 (tiny denominator: 3 nodes, 2 GT
    edges — do not over-read; recorded honestly as a 2-edge anecdote).
  - 6bba@p99.0: edge_raw 0.8462 / adj 0.8670 (18 nodes, 12 GT edges —
    first MEANINGFUL image-based tracking number; trails oracle floor as predicted).
  - Division 1.000 everywhere here (no GT divisions inside probe frames — empty-set convention).
- Timing: 0.75–1.99 s/frame CPU → ×100 frames ≈ 75–200 s/video detection
  alone: OVER the 80–96 s/video envelope unoptimized (H-005 flag; needs
  downsample/ROI/threshold pre-pass before any submit path).

## Decisions
- `keep-trying` — probe only (2 samples × 3 frames). Operating point pct 99.0
  locked for EXP-0008 full-frame sweep + threshold curve. No gate impact
  (probe scale, not a promotion candidate).
