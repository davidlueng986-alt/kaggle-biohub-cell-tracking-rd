# Notes — EXP-0032 Training patch export

## Log
- Scaffolded via `bash scripts/new_experiment.sh EXP-0032 "Training patch export"`.
- `run.sh`: `export_patches.py --out data/patches --seed 0` → `verify_patches.py`.
  Measured: export 86.0 s (462 GT frames), verify 0.4 s (mmap reads).
- Determinism re-run (seed 0 → /tmp, then deleted): MANIFEST md5
  `5e8c5912e27fc2a5026c2f2dae7557d1` identical; per-split shape/sum/first/last
  checksums identical. PASS.

## Decisions
- Patch 16×48×48: ~2.6× cell diameter/axis (cell ~6 z × 25 y/x vox). Context
  for a detector without blowing the 2 GB cap (actual 471 MB).
- Stacked `patches.npy` per embryo split (row-aligned with MANIFEST.csv)
  instead of .npy-per-patch: 2 files vs 6388, same bytes, trivial loading.
- Raw uint16 stored; normalisation deferred to GPU training (per-patch
  z-score or percentile scaling — see train_design.md).
- No DoG recompute for negatives (per mission): max-filter maxima are cheaper
  (0.13 s/frame) and sufficient as hard negatives.
- Splits = embryo ids so GPU training inherits PROTOCOL v1.1 grouping for free.

## Caveats
- 44b6 negatives are 94% easy random-bg (only 11/174 bright-max): sparse
  tissue has few non-GT bright maxima above p98 outside exclusion boxes.
  GPU training should up-sample bright-max or mine online hard negatives.
- GT is sparse/incomplete: unannotated cells can leak into negatives
  (both types). Treat labels as noisy; prefer ranking/contrastive losses.
- 6bba dominates (6040/6388 patches); embryo-balanced sampling needed at
  train time (see train_design.md § anti-overfit).
- Border patches are zero-padded (cells near volume edges); flag via
  manifest coords if the model proves edge-sensitive.
