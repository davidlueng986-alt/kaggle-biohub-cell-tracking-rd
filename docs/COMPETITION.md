# Competition — Biohub: Cell Tracking During Development

- **Slug:** `biohub-cell-tracking-during-development`
- **Title:** Biohub – Cell Tracking During Development
- **Competition page:** https://www.kaggle.com/competitions/biohub-cell-tracking-during-development
- **Metric spec (ground truth):** https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
- **Deadline:** 2026-09-29 23:59 UTC (verify on competition page; observed via `kaggle competitions list` on 2026-09-09)
- **Prize / entrants (observed 2026-09-09):** $60,000 research competition, ~3287 teams

## Rules (code competition)

- **Notebook-only submission**, must run on Kaggle notebooks **without internet access**.
- **Time limit ≤ 12 hours** per run (inference over the hidden test set must fit; plan ≈ 80–96 s/video budget on a T4-class Kaggle GPU).
- No external data at inference time (model weights must be bundled in the notebook / attached datasets).
- See competition page "Rules" tab for the authoritative list (eligibility, team limits, code-reuse rules).

> TODO: re-verify deadline, hardware (GPU type), and timeout from the competition Rules/Data tabs before final submission — links above. Do not rely on this file's cached numbers.

## Data

- **Modality:** 3D + time light-sheet microscopy of developing zebrafish embryos, stored as **OME-Zarr**.
- **Video shape:** `(T, Z, Y, X) = (100, 64, 256, 256)` per sample.
- **Annotations:** `geff`-format tracks (nodes = cell detections with timepoint + centroid; directed edges link a cell at time *t* to itself or its daughters at *t+1*).
- **Train (observed facts from Stage-1 research, re-verify after download):**
  - ~199 samples drawn from **only 2 embryos**: `6bba` (~128 samples), `44b6` (~71 samples).
  - Ground truth is **sparse**: ~2.8 annotated nodes per timepoint; only **~304 divisions** annotated in total.
- **Test:** hidden, **embryo-disjoint** from train (~199 samples from unseen embryos).
- **Consequence:** any split by sample leaks embryo identity. All validation **MUST split by `embryo_id`** (see `docs/PROTOCOL.md`).

> TODO: confirm exact train file layout, `T_true` coarse-count source, and submission sample after `kaggle competitions download` + rules acceptance.

## Submission format

- One `submission.csv` containing **node rows + edge rows** for every test video.
- Exact column schema is NOT reproduced here to avoid inventing it.

> TODO: copy the exact `submission.csv` schema (node/edge row format, parent/daughter encoding, coordinate units) from the competition Data page / sample submission after download, then paste it into this section with a date stamp.

## Metric (summary — normative details live in metrics.md)

Final score (micro-averaged over videos):

```
score = adjusted_edge_jaccard + 0.1 * division_jaccard
```

1. **Node matching:** optimal bipartite assignment by centroid distance, max distance **7 µm**. One-to-one.
2. **Edge matching:** a predicted edge is TP iff both endpoints match GT nodes joined by a GT edge. Every unmatched GT edge is FN. A non-TP predicted edge is FP only in the two sparse-aware cases:
   - its target matches a GT node that is connected to *another* source node, or
   - its source matches a GT node that is connected to *another* target node.
   
   All other predicted edges (e.g. in unannotated regions) are **ignored**. `edge_jaccard = TP / (TP + FP + FN)`.
3. **Adjusted edge Jaccard:** `max(0, jaccard * (1 - 0.1 * (T_pred - T_true) / T_true))`, where `T_true` is a provided coarse estimate of total true nodes and `a = 0.1`. Penalises node-count inflation. Micro-averaged with per-sample weights `w_i = TP_i + FP_i + FN_i`.
4. **Division Jaccard:** a predicted node with ≥ 2 outgoing edges is a predicted fork. GT divisions are evaluated in a local window (`grandparent → dividing parent → children → grandchildren`), allowing a ±1-timepoint fork offset without graph-wide reachability. TP requires local parent anchor + two distinct daughter branches + directed local topology + valid branch evidence + unmerged branches; candidates are paired by maximum-cardinality bipartite matching (one fork ↔ one GT division). FPs include evaluable non-TP forks (matched annotated fork, failed-topology local candidates, cross-component branch evidence, merged branches); structurally valid forks with no local GT evidence are ignored. `division_jaccard = TP / (TP + FP + FN)` on summed counts.
5. **Weight:** division term contributes at most ~0.10 to the final score (weight `w = 0.1`).

## Pitfalls (why naive approaches fail)

1. **Embryo leakage:** train has 2 embryos; sample-wise CV massively overstates generalization. Always split by `embryo_id`.
2. **Division trap:** division term is worth ≤ 0.10, but naive fork prediction *adds* edge-FPs and division-FPs — net negative. Only emit forks with local evidence (see PROTOCOL gates).
3. **Sparse-GT illusion:** predicting dense tracks in unannotated regions is free under edge-FP rules but NOT free under the `T_pred` inflation penalty. Control node count.
4. **7 µm assignment:** centroid localisation error beyond 7 µm breaks node matching and everything downstream. Calibrate voxel→µm scaling per axis.
5. **Temporal leakage:** using frame *t+1* features to predict frame *t* links is invisible in shuffled CV but fatal on hidden embryos. Strict causal direction in models and in CV.
6. **12 h T4 budget:** ~80–96 s/video. Heavy per-video optimisation (e.g. global ILP over 100×64×256×256) must be profiled early; have a fast fallback path.
7. **Public-LB chasing:** hidden test is embryo-disjoint; public LB is a diagnostic, never the objective (see PROTOCOL promotion gates).
