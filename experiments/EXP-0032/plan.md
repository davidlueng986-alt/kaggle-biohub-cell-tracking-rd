# Plan — EXP-0032 Training patch export

## Config / seeds
- Seed export=0, verify=7. Sorted iteration over samples, frames, nodes.
- Patch (z,y,x) = 16×48×48 uint16 (~2.6× cell diameter per axis; cells ~10 µm
  ≈ 6 z × 25 y/x voxels at z=1.625/y=x=0.40625 µm/voxel).
- Negatives 1:1 per frame: half bright non-GT local maxima
  (`scipy.maximum_filter` (3,9,9), per-frame p98 floor, Chebyshev exclusion
  (4,12,12) around GT), half uniform random background; bright-max shortfall
  topped up with random-bg. Zero-pad at volume borders.
- Sampling: NO frame striding — all 462 GT frames processed (measured 0.03 s
  read + 0.13 s max-filter per frame → 86 s total, far under the 25 min cap).
- Splits = embryo ids (`44b6` / `6bba`) to match PROTOCOL v1.1 folds.

## Steps
1. `bash experiments/EXP-0032/run.sh` — runs `export_patches.py` (writes
   `data/patches/<embryo>/patches.npy` + `data/patches/MANIFEST.csv`), then
   `verify_patches.py` (spot-checks, writes `metrics.json`).
2. Cold-rerun check: re-export with `--out` to temp dir, compare MANIFEST md5
   + array checksums (must be identical).
3. Read `train_design.md` before any GPU session; do NOT train on this VM.

## Budget
CPU-only; measured 86 s export + <1 s verify; 471.3 MB on disk (< 2 GB).
No GPU, no pip installs, no Kaggle I/O.
