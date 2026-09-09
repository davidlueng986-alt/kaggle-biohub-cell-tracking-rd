# Notebooks — Kaggle submit path (GOLD §5)

Status: **skeleton** (`submission_skeleton.ipynb`, DRAFT). Nothing here has
been submitted; public LB stays diagnostic-only per PROTOCOL v1.1 §4.

## Files

- `submission_skeleton.ipynb` — offline notebook: config → Hungarian linker
  (7 µm gate) + r10 fork proposals (EXP-0005) → `submission.csv` writer with
  per-video timing. `MODE="demo"` proves wiring on synthetic tracks;
  `MODE="test"` reads `/kaggle/input/.../test/*.zarr` (needs `zarr`,
  `scipy`, `numpy` on the Kaggle image — all standard).
- Format contract (repo side): `scripts/graphs_to_csv.py` writes + `--check`s
  the exact verified schema (`id,dataset,row_type,node_id,t,z,y,x,
  source_id,target_id`). Demo: 4 subset preds → 4294-row valid CSV
  (2026-09-09). Notebook writer mirrors the same column rules inline.

## How to use (cold)

1. Upload this repo (or copy `submission_skeleton.ipynb`) to a Kaggle
   notebook attached to the competition + a dataset containing model weights.
2. Implement `detect()` with the real detector; load weights from
   `/kaggle/input/<weights-dataset>/`. Keep everything offline (no internet
   at submit-rerun) and inside the 12 h budget (~80–96 s/video).
3. Run with `MODE="test"`; confirm row counts + `id` consecutiveness, then
   submit. Record LB as diagnostic + local trusted score in
   `knowledge/RESULTS.md`; never promote on LB alone.

## TODO before first serious submit

- Real detector + bundled weights (H-002 ladder output, GPU-trained).
- Time the full hidden-size run; keep ≥2× headroom (PROTOCOL §7).
- Gate pass on local embryo-CV (worst-fold) + EXP-0006 replication first.
