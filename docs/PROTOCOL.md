# R&D Protocol — FROZEN v1.2

**Status: FROZEN v1.2** (frozen 2026-09-11; supersedes v1.1).
No change to the trusted scorer, CV folds, promotion gates, or trusted-CV envelope without a version bump (v1.3, v2.0…) recorded in the Changelog below and approved in the experiment ledger (`knowledge/RESULTS.md`).

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

## 2. Trusted CV envelope (Grandmaster nested) — MANDATORY

### 2.1 Why v1.2
v1.1 embryo folds were correct in theory, but practice reported **standing** scores (e.g. image adj **0.8194**) from the **same samples used to lock hyperparameters** (DoG percentiles). That is **selection leakage / optimistic CV**, not feature-label leakage. EXP-0021 transfer (worst micro **0.341**) and public LB **~0.65–0.67** exposed the optimism. External public LB (e.g. Lineage Forge **0.946**) is **not** a trusted target — treat as `lb_external_untrusted` (possible public-LB overfit / unknown stack).

### 2.2 Score tags (`cv_tag`)
Every reported number MUST carry one tag:

| Tag | Meaning | May set standing / promote? |
|-----|---------|------------------------------|
| `trusted` | Nested CV per §2.3–2.4; HPs fit without eval samples | **YES** |
| `tuned_ref` | HPs tuned on (or chosen using) the scored samples | NO — log only |
| `oracle` | Uses GT nodes / non-submittable oracles | NO |
| `lb_diagnostic` | Our own public LB after a submit | Observe only (§4) |
| `lb_external_untrusted` | Other notebooks / other accounts' public LB | Hypothesis fuel only |

**Standing image / model numbers may only be `trusted`.** Retag historical 0.8194-class results as `tuned_ref`.

### 2.3 Nested hyperparameter rule
Free HPs include (non-exhaustive): DoG percentile(s), link gate µm, fork thresholds, intensity calibrators, early-stopping epochs, post-process cutoffs.

- Fitting / selecting any free HP using statistics or scores from an evaluation sample (or its embryo, when the fold requires embryo holdout) → result is at most `tuned_ref`.
- Learned models: train weights on the fold's train embryos only; early-stop / model-select on a **within-train** split (sample or time block), never on the holdout embryo.
- Fixed constants from the competition pin (voxel scale, 7 µm match, `a=0.1`) are **not** free HPs.

### 2.4 Required trusted metrics (report all three)
On the current subset (6 samples: 3×`44b6` + 3×`6bba`; expand when more data lands):

1. **`loso_micro`** — Leave-One-Sample-Out micro-average:
   - For each held-out sample `S`: fit all free HPs on the other samples **only** (default search grid documented in `scripts/trusted_cv.py`), freeze, score `S` with trusted scorer v1.1.
   - Micro-average across all held-out `S` with weights `w_i = TP_i+FP_i+FN_i` (same as scorer).
2. **`loso_worst`** — minimum per-sample trusted score under the same LOSO protocol (shake-up proxy).
3. **`embryo_nested`** — embryo LOEO with nested HPs:
   - fold0: fit HPs on all `6bba` subset samples only → score all `44b6` subset samples → embryo micro.
   - fold1: symmetric.
   - Report **worst** of fold0/fold1 embryo micros as `embryo_nested_worst`.

Primary ranking key for standing / BTE: **`loso_worst`**, then `loso_micro`, then `embryo_nested_worst`.

### 2.5 Embryo folds (unchanged topology; nested HPs required)
Train still comes from **2 embryos** (`6bba`, `44b6`). Splitting by sample for **learned weights** still leaks embryo identity and remains forbidden for weight training.

| Fold | Train embryos | Holdout embryo | Purpose |
|------|---------------|----------------|---------|
| fold0 | `6bba` | `44b6` | primary generalisation gate |
| fold1 | `44b6` | `6bba` | stability check |

- Group key is `embryo_id` for weight training. Within-embryo temporal order preserved.
- **Difference from v1.1 practice:** holdout scores are only `trusted` if HPs were nested (§2.3). A fold score with HPs locked on the holdout embryo is `tuned_ref`.

### 2.6 Harness
- Canonical runner: `scripts/trusted_cv.py` (plus thin wrappers). Experiments MUST call it (or an audited equivalent) for any `cv_tag: trusted` claim.
- Output JSON must include: `protocol_version`, `cv_tag`, `loso_micro`, `loso_worst`, `embryo_nested_worst`, per-sample LOSO table, HP-fit provenance per fold/left-out sample, scorer version.

## 3. Temporal causality

- Models and features at time *t* may use frames ≤ *t* only (plus an explicit, declared smoothing window if ablated as a hypothesis — default: none).
- Linking/association may run forward passes; any backward-correction pass must be declared in the experiment plan and ablated (with vs without).
- `scripts/` data loaders MUST NOT expose future frames to the model call path; Stage-3 dry run should assert this (e.g. a test that future-frame access raises).

## 4. Anti-shakeup promotion gates

A candidate promotes (hypothesis → accepted → ensemble candidate) **iff all** hold:

1. **Local trusted win:** beats the current best **`trusted`** standing on **`loso_worst`** (primary) and does not regress `loso_micro` beyond tolerance (default: 0 absolute). Win must replicate across **≥ 2 seeds** when stochastic; single-seed wins do not count. `tuned_ref` / `oracle` / LB numbers never satisfy this gate.
2. **Embryo nested stability:** does not regress vs baseline on **`embryo_nested_worst`** beyond tolerance (default: 0 absolute regression).
3. **Diversity (for ensemble admission):** candidate must add a *different* error profile — measured by disagreement with current ensemble on edge-FN sets (or division-TP sets) — not just a higher mean. Near-duplicate predictions are rejected even with small wins.
4. **LB diagnostic only:** our own public LB may be *observed* after gates 1–3 pass, to detect scorer-mirror bugs or CV miscalibration (`|loso_micro − public_lb| > 0.15` → flag `cv_lb_miscalibrated`, investigate before ship). LB movement alone never promotes / demotes. **External public LB (Forge etc.) never promotes, never sets targets.**
5. **Division sub-gate:** any change that increases predicted-fork count must show division-Jaccard gain AND no adjusted-edge-Jaccard regression under the trusted envelope on both embryo sides. Fork-count inflation without division gain is an automatic reject.

## 5. Ensemble / selection / BTE policy

- **BTE (Beat The Existing trusted):** the number to beat is our current best **`trusted`** envelope — **not** Forge 0.946, **not** public LB, **not** historical `tuned_ref` 0.8194.
- Final selection maximises **`loso_worst`**, then `loso_micro`, then `embryo_nested_worst` — shake-up resistance over peak.
- Ensemble members chosen for **stability + diversity**: prefer 2–4 members with uncorrelated edge errors under LOSO over N copies of the best single seed.
- Fusion method must itself pass gates 1–3 as if it were a model.
- Keep a **fast fallback** single model that fits the 12 h budget with ≥ 2× headroom; the ensemble is only submitted if it fits the per-video time budget (§7) end-to-end in a dry run.
- Seeds: every stochastic trusted number is mean ± range over ≥ 2 seeds; the submitted artefact pins one seed per member.
- Ledger: `knowledge/LB_CALIBRATION.md` records each of **our** (trusted_cv, public_lb) pairs; external LB goes to a separate untrusted table.

## 6. Leakage checklist (run before every promotion)

- [ ] Split key for weight training is `embryo_id` (no sample-wise weight split that mixes holdout embryo).
- [ ] All free HPs nested per §2.3; metrics tagged `trusted` (not `tuned_ref`).
- [ ] No test-embryo / held-out-sample statistics used in training or tuning for that fold/LOSO step.
- [ ] No future-frame features in causal path (or ablation declared).
- [ ] Track IDs / lineage labels from GT never input as features.
- [ ] `T_true` / normalisation constants come from train / non-held-out samples only for that step.
- [ ] Notebook path re-runs offline (no internet) within the 12 h budget; per-video time logged.
- [ ] Scorer version pinned in `metrics.json` (protocol version + scorer git hash).
- [ ] BTE compared against trusted standing, not external LB.

## 7. Compute budget

- VM (this machine): Python 3.13, **no GPU**, 113 GB free — for scorer dev, EDA on samples, dry runs. No full training here.
- Kaggle notebooks (submission + exploration): **≤ 12 h, no internet**, T4-class GPU. Per-video inference budget **≈ 80–96 s** (199 videos).
- Policy: profile per-video latency in every experiment's `metrics.json` (`infer_s_per_video`); any experiment exceeding budget must either slim down or be marked non-submittable. Stage-3 dry run (EXP-0001) establishes the timing harness on CPU with a scale factor noted.

## Changelog

- **v1.2 (2026-09-11):** Trusted-CV rebuild (Grandmaster nested). Mandatory `cv_tag`; LOSO + embryo-nested metrics (`loso_micro`, `loso_worst`, `embryo_nested_worst`); nested HP rule; BTE vs trusted standing only; external LB (e.g. Forge 0.946) marked untrusted and never a target; promotion gates rekeyed to trusted envelope; LB calibration ledger. Scorer v1.1.0 unchanged. Historical standing 0.8194 reclassified `tuned_ref`.
- **v1.1 (2026-09-09):** Faithful scorer (`scripts/score.py` v1.1.0 + `scripts/test_score.py` 13 tests): per-timepoint 7 µm Hungarian matching with pinned voxel scale, sparse-aware edge FP, `T_true` penalty (`estimated_number_of_nodes`), division local-window with max-cardinality pairing, submission.csv micro-average, legacy-toy backward compat. EXP-0001 re-scored (hand-calc still 0.5/1.0/0.6, still keep-trying); EXP-0002 validates geometric path. Gates/folds unchanged.
- **v1.0 (2026-09-09):** Initial frozen protocol. Trusted scorer = exact mirror of `metrics.md` (edge + adjusted + division + micro-average); embryo-level folds (fold0 holdout `44b6`, fold1 holdout `6bba`); causality rule; 5 promotion gates incl. division sub-gate; worst-fold ensemble selection; leakage checklist; compute budget. Open TODOs: µm scaling constants, `T_true` provenance, `submission.csv` schema (all link to competition data / metrics.md).
