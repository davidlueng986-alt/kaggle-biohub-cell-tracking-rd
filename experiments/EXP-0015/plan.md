# Plan — EXP-0015 Appearance probe

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0 labels (via `scripts/appearance.py`
  mirroring score.py exactly). Deterministic.
- Graph: EXP-0009 `full_6bba_05b6850b_pred.json` (frozen @98.5) + EXP-0003 GT.
  Images: `data/train/6bba_05b6850b.zarr` (cached per timepoint).
- Patch radius (4,10,10) vox (~cell scale). NCC per edge; distance recorded
  as the geometry-only covariate.

## Cold-run steps

1. `bash experiments/EXP-0015/run.sh` → `metrics.json` (NCC stats by
   class, separation verdict).
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, ~10 min (timepoint caching; ~4.3k edges × small patches).
