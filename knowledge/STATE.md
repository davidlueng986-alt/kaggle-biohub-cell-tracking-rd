# STATE — cold resume in ≤5 min

Last updated: 2026-09-09 (PM GOLD: EXP-0004 sub-gate reject, signal kept). Maintainer: gold-watch.
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
- Subset download DONE 2026-09-09 (PROMPT-GOLD §1, after early-stop fix): 6 ids (3×44b6 + 3×6bba, embryo-paired), 738/738 files ok 0 fail, 2.6 GB in `data/` (gitignored). EDA needs `pip install zarr numcodecs` — DONE (zarr 3.3.0 on VM).
- Never commit secrets. See `docs/AUTH.md`.
- Never commit secrets. See `docs/AUTH.md`.

## What exists

- `docs/`: PROTOCOL.md (FROZEN v1.1), COMPETITION.md (submission schema + voxel + T_true verified 2026-09-09), AUTH.md.
- `scripts/`: score.py v1.1.0 (faithful), test_score.py (13 tests, all pass), run_loop.sh, new_experiment.sh. `requirements.txt` (numpy>=2.0).
- `experiments/EXP-0000/`: template; `run_loop.sh --dry-run` validates it.
- `experiments/EXP-0001/`: DONE — legacy toy harness re-scored under v1.1 (fold0 0.5/1.0/0.6 hand-calc match, `dry_run:true`, keep-trying). Do not recreate.
- `experiments/EXP-0002/`: DONE 2026-09-09 — full-scorer geometric validation (H-001+H-004): perfect 1.1 / idswitch 0.333 (FP≥1) / inflated adj 0.9 / division TP then FN; 6/6 checks pass; `dry_run:true`, keep-trying (no real data, NOT promotable).
- `experiments/EXP-0003/`: DONE 2026-09-09 — FIRST REAL-DATA result (H-001+H-002): oracle GT nodes + causal Hungarian linker on subset 6 → 44b6-micro 1.0933 / 6bba-micro 1.0705 / worst 1.0705; div 0/0/4 (no forks); `real_data:true`, keep-trying (floor, not a model). Helpers: `scripts/geff_to_graph.py`, `scripts/baseline_link.py`.
- `experiments/EXP-0004/`: DONE 2026-09-09 — fork-proposing variant (H-002+H-003, `scripts/fork_link.py --propose-um 15.0`): fold0 44b6 unchanged (+0.0000), fold1 6bba micro −0.0025, div sums 0/0/4→3/10/1. Sub-gate REJECT for promotion (edge regression on fold1; single-seed cap anyway). Signal kept: 3/4 GT divisions geometrically recoverable → EXP-0005 tighter gating.
- `knowledge/`: this file + HYPOTHESES.md (H-001/H-004/H-002/H-003 active, H-005 backlog) + RESULTS.md (EXP-0000…0004 rows).
- `opencode-web.png`: local screenshot, git-ignored (not deleted).
- Subset download DONE 2026-09-09 (738/738, 2.6 GB in `data/`, gitignored). EDA deps installed (zarr 3.3.0 + numcodecs, CPU-only).

## Current best

Oracle-linker floor (real data, NOT promotable — beat this):
- EXP-0003: worst-fold edge 1.0705 (44b6 1.0933 / 6bba 1.0705), division 0/0/4.
- EXP-0004 fork variant: fold0 +0.0000, fold1 −0.0025, div 3/10/1 → sub-gate REJECT (signal: 3/4 divisions recoverable; noise must go).
- Harness (toy): EXP-0001 0.600/0.333; EXP-0002 perfect 1.1, idswitch 0.333.
- Next: EXP-0005 tighter fork gating (smaller radius / component veto / appearance); then Kaggle notebook skeleton (GOLD §§4–5).

## Next loop steps (cold agent — copy/paste)

```bash
cat knowledge/STATE.md knowledge/HYPOTHESES.md knowledge/RESULTS.md
cat docs/PROTOCOL.md docs/COMPETITION.md docs/AUTH.md PROMPT-GOLD.md
ls experiments/ data/train/
# Auth checks (both WORKS 2026-09-09):
export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"
gh auth status
# Download watch: tail -n 5 /tmp/biohub-subset-dl.log  (expect DONE ok 738 fail 0)
# Loop (EXP-0001…0004 done — read them, don't recreate):
bash scripts/run_loop.sh --dry-run
python3 scripts/score.py --dry-run
python3 scripts/test_score.py
# New experiment (EXP-0005 tighter fork gating):
bash scripts/new_experiment.sh EXP-0005 "<title>"
```
