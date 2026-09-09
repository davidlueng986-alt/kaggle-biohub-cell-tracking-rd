# R&D Protocol — FROZEN v1.1

**Status: FROZEN v1.1** (frozen 2026-09-09; supersedes v1.0).
No change to the trusted scorer, CV folds, or promotion gates without a version bump (v1.2, v2.0…) recorded in the Changelog below and approved in the experiment ledger (`knowledge/RESULTS.md`).

Normative metric reference: https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
Competition facts: see `docs/COMPETITION.md`.

## 1. Trusted scorer definition

- `scripts/score.py` v1.1.0 is the **only** number that can promote a model. Public LB is diagnostic only (§4).
- The scorer mirrors `metrics.md` exactly, with competition-page pins (verified 2026-09-09):
  - Node matching: **per-timepoint** optimal bipartite assignment (Hungarian, pure-python + numpy, no scipy) on **scaled centroid distance** with voxel scale **z=1.625, y=0.40625, x=0.40625 µm/voxel**, threshold **7 µm** inclusive, one-to-one.
  - Edge TP/FP/FN with the sparse-aware FP rule (only the two listed cases count as FP; all other non-TP predicted edges ignored).
  - Adjusted edge Jaccard with `a = 0.1`, `max(0, …)` floor (NO upper cap — scores can exceed 1.0), micro-averaging with weights `w_i = TP_i + FP_i + FN_i`. `T_true` = `estimated_number_of_nodes` from `.geff` `zarr.json`; missing `T_true` → unpenalized with `T_true_used:false` flag (non-promotable until pinned).
  - Division Jaccard with the local-window (±1 timepoint) fork logic: parent anchor, two distinct daughter branches, directed local topology, branch-evidence validity, unmerged-branch requirement, maximum-cardinality fork↔GT pairing; summed TP/FP/FN. Conservative approximation documented in `score.py` header (global per-t match restricted to window; weakly-connected GT components for cross-component evidence — never inflates TPs).
  - Final: `score = adjusted_edge_jaccard + 0.1 * division_jaccard`.
  - I/O: JSON geff-like single-sample graphs + `submission.csv` multi-sample (grouped by `dataset`) micro-average; legacy ID-tuple toy JSON still scores via flagged `simplified:true` path so EXP-0001 hand-calc (0.5/1.0/0.6) keeps passing.
  - Tests: `scripts/test_score.py` (13 tests, stdlib unittest) must pass before any promotion; `score.py --dry-run` runs legacy toy + geometric smoke (1-voxel y-offset must match).
  - Node matching: optimal bipartite assignment on centroid distance, threshold **7 µm**, one-to-one.
  - Edge TP/FP/FN with the sparse-aware FP rule (only the two listed cases count as FP; all other non-TP predicted edges ignored).
  - Adjusted edge Jaccard with `a = 0.1`, `max(0, …)` floor, micro-averaging with weights `w_i = TP_i + FP_i + FN_i`.
  - Division Jaccard with the local-window (±1 timepoint) fork logic: parent anchor, two distinct daughter branches, directed local topology, branch-evidence validity, unmerged-branch requirement, maximum-cardinality fork↔GT pairing; summed TP/FP/FN.
  - Final: `score = adjusted_edge_jaccard + 0.1 * division_jaccard`.
- Implementation rules:
  - One function per metric stage (node-match → edge-counts → adjustment → division-counts → aggregate) so each stage is unit-testable against hand-worked examples.
  - Deterministic: fixed seeds, no wall-clock dependence, sorted iteration.
  - Score output is a JSON with per-sample counts AND aggregates (never a bare float), so failures are auditable.
  - Any deviation from `metrics.md` discovered later is a scorer bug → fix, bump protocol version, re-score all prior experiments.

> Source pins (verified 2026-09-09): voxel scale + T_true provenance + submission schema in `docs/COMPETITION.md` (Evaluation/Data tabs + sample_submission.csv). Scorer defaults match these pins; override via `--voxel` / `--T-true` only as an explicit hypothesis ablation.

## 2. Cross-validation folds (group-aware, embryo-level)

Train comes from ~199 samples of **2 embryos** (`6bba` ~128, `44b6` ~71). Splitting by sample leaks embryo identity and is **forbidden**.

| Fold | Train embryos | Holdout embryo | Purpose |
|------|---------------|----------------|---------|
| fold0 | `6bba` | `44b6` | primary gate: generalisation to unseen embryo |
| fold1 | `44b6` | `6bba` | stability check (train-small direction) |

- Group key is `embryo_id`; all samples of one embryo stay together. No stratification by sample.
- Within-embryo temporal order is preserved; no shuffling of timepoints across the train/holdout boundary.
- fold0 is the **promotion fold**; fold1 guards against single-embryo luck. With only 2 embryos, both folds are required for promotion (§4).
- If more embryos become available (e.g. pseudo-labelled or external data), add folds as leave-one-embryo-out and bump the protocol version — never convert to sample-wise k-fold.

## 3. Temporal causality

- Models and features at time *t* may use frames ≤ *t* only (plus an explicit, declared smoothing window if ablated as a hypothesis — default: none).
- Linking/association may run forward passes; any backward-correction pass must be declared in the experiment plan and ablated (with vs without).
- `scripts/` data loaders MUST NOT expose future frames to the model call path; Stage-3 dry run should assert this (e.g. a test that future-frame access raises).

## 4. Anti-shakeup promotion gates

A candidate promotes (hypothesis → accepted → ensemble candidate) **iff all** hold:

1. **Local win:** beats the current best trusted-scorer `score` on **fold0 holdout** (`44b6`) by a margin ≥ noise threshold (default: win must replicate across **≥ 2 seeds**; single-seed wins do not count).
2. **Stability across folds:** does not regress vs baseline on **fold1 holdout** (`6bba`) beyond tolerance (default tolerance: 0 absolute regression on `score`; any fold1 regression → needs explicit justification + version bump note).
3. **Diversity (for ensemble admission):** candidate must add a *different* error profile — measured by disagreement with current ensemble on edge-FN sets (or division-TP sets) — not just a higher mean. Near-duplicate predictions are rejected even with small wins.
4. **LB diagnostic only:** public LB may be *observed* after gates 1–3 pass, to detect scorer-mirror bugs (local≫LB divergence). LB movement alone never promotes, and LB regression alone never demotes, a gate-passing candidate.
5. **Division sub-gate (division trap guard):** any change that increases predicted-fork count must show division-Jaccard gain AND no adjusted-edge-Jaccard regression on both folds. Fork-count inflation without division gain is an automatic reject.

## 5. Ensemble / selection policy

- Final selection maximises **worst-fold trusted score** (min of fold0/fold1), not mean — shake-up resistance over peak.
- Ensemble members chosen for **stability + diversity**: prefer 2–4 members with uncorrelated edge errors across folds over N copies of the best single seed.
- Fusion method (e.g. per-edge majority / tracklet voting) must itself pass gates 1–3 as if it were a model.
- Keep a **fast fallback** single model that fits the 12 h budget with ≥ 2× headroom; the ensemble is only submitted if it fits the per-video time budget (§6) end-to-end in a dry run.
- Seeds: every reported number is mean ± range over ≥ 2 seeds; the submitted artefact pins one seed per member.

## 6. Leakage checklist (run before every promotion)

- [ ] Split key is `embryo_id` (no sample-wise split anywhere in the experiment).
- [ ] No test-embryo statistics (means, normalisation, thresholds) used in training or tuning.
- [ ] No future-frame features in causal path (or ablation declared).
- [ ] Track IDs / lineage labels from GT never input as features.
- [ ] `T_true` / normalisation constants come from train embryos only.
- [ ] Notebook path re-runs offline (no internet) within the 12 h budget; per-video time logged.
- [ ] Scorer version pinned in `metrics.json` (protocol version + scorer git hash).

## 7. Compute budget

- VM (this machine): Python 3.13, **no GPU**, 113 GB free — for scorer dev, EDA on samples, dry runs. No full training here.
- Kaggle notebooks (submission + exploration): **≤ 12 h, no internet**, T4-class GPU. Per-video inference budget **≈ 80–96 s** (199 videos).
- Policy: profile per-video latency in every experiment's `metrics.json` (`infer_s_per_video`); any experiment exceeding budget must either slim down or be marked non-submittable. Stage-3 dry run (EXP-0001) establishes the timing harness on CPU with a scale factor noted.

## Changelog

- **v1.1 (2026-09-09):** Faithful scorer (`scripts/score.py` v1.1.0 + `scripts/test_score.py` 13 tests): per-timepoint 7 µm Hungarian matching with pinned voxel scale, sparse-aware edge FP, `T_true` penalty (`estimated_number_of_nodes`), division local-window with max-cardinality pairing, submission.csv micro-average, legacy-toy backward compat. EXP-0001 re-scored (hand-calc still 0.5/1.0/0.6, still keep-trying); EXP-0002 validates geometric path. Gates/folds unchanged.
- **v1.0 (2026-09-09):** Initial frozen protocol. Trusted scorer = exact mirror of `metrics.md` (edge + adjusted + division + micro-average); embryo-level folds (fold0 holdout `44b6`, fold1 holdout `6bba`); causality rule; 5 promotion gates incl. division sub-gate; worst-fold ensemble selection; leakage checklist; compute budget. Open TODOs: µm scaling constants, `T_true` provenance, `submission.csv` schema (all link to competition data / metrics.md).
