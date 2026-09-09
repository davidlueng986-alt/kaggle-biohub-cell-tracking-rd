# Plan — EXP-0003 Real-data oracle-linker baseline

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic (no randomness, no seeds).
- Subset (data/, gitignored): 44b6_0113de3b, 44b6_0b24845f, 44b6_0c582fdc,
  6bba_05b6850b, 6bba_05db0fb1, 6bba_062c8d37 (full .zarr + .geff, 738 files).
- GT graphs: `scripts/geff_to_graph.py --all data/train --out-dir experiments/EXP-0003/gt`
  (T_true from `estimated_number_of_nodes`; voxel pinned).
- Preds: `scripts/baseline_link.py <gt> --out <pred>` per sample (causal,
  adjacent-frame only, 7 µm gate).
- Scores: `scripts/score.py --pred <pred> --gt <gt> --out <scores>` per sample;
  embryo aggregates via micro-average (44b6 n=3, 6bba n=3) + worst-fold.

## Cold-run steps

1. `bash experiments/EXP-0003/run.sh` (does all of the above + asserts +
   writes `metrics.json`).
2. `bash scripts/run_loop.sh --dry-run`.
3. Both exit 0.

## Budget

- CPU-only (linker + scorer on GT graphs, seconds–minutes). Images in
  `data/train/*.zarr` are NOT read by this baseline (oracle detections).
  Real image-based detection/training belongs in Kaggle notebooks (GPU).
