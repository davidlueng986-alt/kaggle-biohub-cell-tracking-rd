# Notes — EXP-0048 harvest readiness drill

## Log
- Random-weight infer: 25,745 nodes / 3 frames in 227s (thr 0.3 far too low for random
  heatmaps: 8.5k/frame garbage vs ~50 GT — expected, not a detector verdict).
- Link step died silently on 8.5k^2 Hungarian (OOM-infeasible by design); skipped, decision-irrelevant.
- Wiring proven: zarr -> heatmap -> peak json. gitignore + status checks OK; weights still absent.

## Decisions
- READY: when unet_best.pt lands, run EXP-0035 full eval (real weights -> sparse dets -> link).
- Re-run rule: cap top-K/frame before any random-weight link test.
