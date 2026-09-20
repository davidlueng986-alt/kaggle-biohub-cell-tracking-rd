# HF Manifest

> No HF dataset/model URLs are recorded yet — no push has landed.
> Do NOT invent repo URLs. Fill the table below when the first
> `huggingface-cli` upload completes (record exact repo + revision).

| HF repo | path / revision | local destination | notes |
|---------|-----------------|-------------------|-------|
| (none yet) | — | `data/` | first push pending; local subset only |

Local subset currently present (untracked blobs):

- `data/train/`: 6 sequences (`44b6_0113de3b`, `44b6_0b24845f`,
  `44b6_0c582fdc`, `6bba_05b6850b`, `6bba_05db0fb1`, `6bba_062c8d37`)
- `data/patches/`: `44b6/patches.npy`, `6bba/patches.npy`, `MANIFEST.csv`
- `data/weights/`: `unet_best.pt`, `unet_v10_timeout_last.pt`

Pull example (after repos exist — replace `<DATASET_REPO>` with the real repo):

```bash
huggingface-cli download <DATASET_REPO> --local-dir data/hf --repo-type dataset
```

Auth note: use `HF_TOKEN` from the environment / secret store at runtime.
Never commit tokens, `kaggle.json`, or `.env` files (see `.gitignore`).
