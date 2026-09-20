# Data (pointers only — blobs not stored in git)

Large train/test artifacts are **not** stored in git. See `HF_MANIFEST.md`.

Local layout (observed 2026-09-20, subset checkout):

- `data/train/` — 6 sequence dirs, each with `.zarr/` + `.geff/` pair
  (e.g. `44b6_0113de3b`, `6bba_05b6850b`; see `SUBSET_IDS.txt`)
- `data/patches/` — `44b6/patches.npy`, `6bba/patches.npy`, `MANIFEST.csv`
- `data/weights/` — local training checkpoints (untracked, reproducible)
- `data/sample_submission.csv`, `data/SUBSET_FILES.txt`,
  `data/SUBSET_IDS.txt`, `data/zarr.json` — small pointer/subset files (untracked)
- `data/README.md`, `data/HF_MANIFEST.md` — tracked pointer docs (this file + manifest)

Only `README.md` and `HF_MANIFEST.md` under `data/` are git-tracked
(via `!data/README.md` / `!data/HF_MANIFEST.md` exceptions in `.gitignore`).
Everything else under `data/` is ignored. No credentials are stored here.
