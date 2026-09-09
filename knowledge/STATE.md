# STATE — cold resume in ≤5 min

Last updated: 2026-09-09 (PM GOLD watch: gh unblocked, subset DL 450/738). Maintainer: gold-watch.
Prior: scorer v1.1 + EXP-0002 green. `PROMPT-RD-SYSTEM.md` done; active brief is `PROMPT-GOLD.md` (continuous gold run, PM owns go).

## Goal

Build a durable auto R&D loop (hypothesize → operationalize → execute → trusted score → update knowledge)
for Kaggle **Biohub – Cell Tracking During Development**, not a one-off notebook.

## Competition

- Slug: `biohub-cell-tracking-during-development` (code-competition).
- Page: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development
- Metric spec (normative): https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
- Metric: `score = adjusted_edge_jaccard + 0.1 * division_jaccard` (per-timepoint 7 µm match, voxel z=1.625/y=x=0.40625, sparse-aware edge FP, `a=0.1` T_true penalty with T_true=`estimated_number_of_nodes`, division local-window ±1tp; micro-averaged; scores CAN exceed 1.0).
- Train: ~199 samples from **2 embryos only** (`6bba` ~128, `44b6` ~71) → embryo-grouped CV mandatory; frame-random splits leak. Format: OME-Zarr v3 `(100,64,256,256)` + `.geff` (`nodes/ids`, `nodes/props/{t,z,y,x}/values`, `edges/ids`); folders `{embryo}_{fov}`.
- Test: hidden, **embryo-disjoint** from train. Notebook-only submission, ≤12 h, no internet, ~80–96 s/video budget. Submission CSV: `id,dataset,row_type,node_id,t,z,y,x,source_id,target_id` (verified from sample_submission.csv 2026-09-09).
- Details: `docs/COMPETITION.md`. Deadline observed 2026-09-29 23:59 UTC (re-verify on competition page). Entry observed True, ~3287 teams, $60k (2026-09-09).

## Protocol pointer

- **FROZEN v1.1**: `docs/PROTOCOL.md` (faithful scorer v1.1.0: per-timepoint 7 µm Hungarian, pinned voxel, T_true=`estimated_number_of_nodes`, division window, submission.csv micro-average; embryo folds fold0 holdout `44b6` / fold1 holdout `6bba`; causality rule; 5 promotion gates; worst-fold ensemble; leakage checklist; compute budget).
- Competition facts: `docs/COMPETITION.md`. Auth steps: `docs/AUTH.md`.
- Loop runner: `bash scripts/run_loop.sh --dry-run` (script is `.sh`, takes no `--exp` flag).
- Scaffolder: `bash scripts/new_experiment.sh EXP-XXXX "title"`.
- Scorer `scripts/score.py` v1.1.0 + `scripts/test_score.py` (13 tests) — both must pass before any promotion. Legacy toy path kept for EXP-0001 hand-calc.
- Promotion gated on local trusted scorer + cross-fold stability; public LB is diagnostic only.

## Env

- Python 3.13.5 (verified `python3 --version`), **no GPU**, ~113 GB free. No full training on this VM.
- `requirements.txt`: `numpy>=2.0` only (no torch/scipy; GPU/Kaggle-notebook extras commented). No installs run by repo-hardener.
- `scripts/` contains: `score.py`, `run_loop.sh`, `new_experiment.sh` (no `run_loop.py` — correct any such reference to `.sh`).
- CI: `.github/workflows/smoke.yml` runs scorer dry-run + `run_loop.sh --dry-run` + guarded `test_score.py` (skips if absent) + JSON validation.

## Auth status (verification commands — re-run, do not assume)

- Kaggle CLI (`~/.local/bin/kaggle`): **WORKS (verified 2026-09-09 by repo-hardener: `kaggle competitions list --search "biohub"` exit 0, returned `biohub-cell-tracking-during-development`, userHasEntered=True)**:
  `export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"`
  then `kaggle competitions download -c biohub-cell-tracking-during-development -p data/` (requires Rules acceptance on competition page first).
- `gh`: **WORKS (verified 2026-09-09: logged in as davidlueng986-alt, remote HEAD in sync)**. Repo: https://github.com/davidlueng986-alt/kaggle-biohub-cell-tracking-rd (exists). Push frequent small commits.
- Subset download (PROMPT-GOLD §1, restarted after early-stop fix — `scripts/download_subset.py` no longer stops while ids missing): target ids in `data/SUBSET_IDS.txt` = `44b6_0113de3b, 44b6_0b24845f, 44b6_0c582fdc, 6bba_05b6850b, 6bba_05db0fb1, 6bba_062c8d37` (3×44b6 + 3×6bba, embryo-paired). 738 files (`data/SUBSET_FILES.txt`); progress ~450/738 ok, 0 fail (see `/tmp/biohub-subset-dl.log`). Full `.zarr` + `.geff` per sample into `data/` (gitignored). Do NOT download full ~88GB.
- Never commit secrets. See `docs/AUTH.md`.
- Never commit secrets. See `docs/AUTH.md`.

## What exists

- `docs/`: PROTOCOL.md (FROZEN v1.1), COMPETITION.md (submission schema + voxel + T_true verified 2026-09-09), AUTH.md.
- `scripts/`: score.py v1.1.0 (faithful), test_score.py (13 tests, all pass), run_loop.sh, new_experiment.sh. `requirements.txt` (numpy>=2.0).
- `experiments/EXP-0000/`: template; `run_loop.sh --dry-run` validates it.
- `experiments/EXP-0001/`: DONE — legacy toy harness re-scored under v1.1 (fold0 0.5/1.0/0.6 hand-calc match, `dry_run:true`, keep-trying). Do not recreate.
- `experiments/EXP-0002/`: DONE 2026-09-09 — full-scorer geometric validation (H-001+H-004): perfect 1.1 / idswitch 0.333 (FP≥1) / inflated adj 0.9 / division TP then FN; 6/6 checks pass; `dry_run:true`, keep-trying (no real data, NOT promotable).
- `knowledge/`: this file + HYPOTHESES.md (H-001 active, H-004 active, H-002/H-003/H-005 backlog) + RESULTS.md (EXP-0000/0001/0002 rows).
- `opencode-web.png`: local screenshot, git-ignored (not deleted).
- Real-data subset IN PROGRESS (see Auth status): 6 train samples downloading; EXP-0003 baseline starts when all 6 complete. EDA needs `pip install zarr numcodecs` (not yet installed; CPU-only, fine on VM).

## Current best

None yet (real-data best). Harness results (NOT promotable):
- EXP-0001 legacy toy: fold0 0.600 / fold1 0.333 (hand-calc match).
- EXP-0002 geometric (v1.1): perfect 1.1, idswitch 0.333, inflated-adj 0.9, division TP→FN. Next promotable target: EXP-0003 real embryo-CV baseline after Rules acceptance + download.

## Next loop steps (cold agent — copy/paste)

```bash
cat knowledge/STATE.md knowledge/HYPOTHESES.md knowledge/RESULTS.md
cat docs/PROTOCOL.md docs/COMPETITION.md docs/AUTH.md PROMPT-GOLD.md
ls experiments/ data/train/
# Auth checks (both WORKS 2026-09-09):
export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"
gh auth status
# Download watch: tail -n 5 /tmp/biohub-subset-dl.log  (expect DONE ok 738 fail 0)
# Loop (EXP-0001/0002 done — read them, don't recreate):
bash scripts/run_loop.sh --dry-run
python3 scripts/score.py --dry-run
python3 scripts/test_score.py
# New experiment (EXP-0003 real-data baseline once subset completes):
bash scripts/new_experiment.sh EXP-0003 "<title>"
```
