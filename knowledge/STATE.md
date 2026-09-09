# STATE — cold resume in ≤5 min

Last updated: 2026-09-09. Maintainer: knowledge-synthesizer (Stage 2→3 handoff).
Prior: repo-scaffolder-structure skeleton (no runs yet). `PROMPT-RD-SYSTEM.md` untouched.

## Goal

Build a durable auto R&D loop (hypothesize → operationalize → execute → trusted score → update knowledge)
for Kaggle **Biohub – Cell Tracking During Development**, not a one-off notebook.

## Competition

- Slug: `biohub-cell-tracking-during-development` (code-competition).
- Page: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development
- Metric spec (normative): https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
- Metric: `score = adjusted_edge_jaccard + 0.1 * division_jaccard` (7 µm node match, sparse-aware edge FP rule, `a=0.1` T_true penalty, division local-window ±1 tp; micro-averaged).
- Train: ~199 samples from **2 embryos only** (`6bba` ~128, `44b6` ~71) → embryo-grouped CV mandatory; frame-random splits leak.
- Test: hidden, **embryo-disjoint** from train. Notebook-only submission, ≤12 h, no internet, ~80–96 s/video budget.
- Details: `docs/COMPETITION.md`. Deadline observed 2026-09-29 23:59 UTC (re-verify on competition page).

## Protocol pointer

- **FROZEN v1.0**: `docs/PROTOCOL.md` (trusted scorer mirror of metrics.md, embryo folds fold0 holdout `44b6` / fold1 holdout `6bba`, causality rule, 5 promotion gates, worst-fold ensemble selection, leakage checklist, compute budget).
- Competition facts: `docs/COMPETITION.md`. Auth steps: `docs/AUTH.md`.
- Loop runner: `bash scripts/run_loop.sh --dry-run` (NOTE: script is `.sh`, takes no `--exp` flag; old `run_loop.py --exp` references are stale — see README fix 2026-09-09).
- Scaffolder: `bash scripts/new_experiment.sh EXP-XXXX "title"`.
- Scorer `scripts/score.py` is **SIMPLIFIED** (plain set-Jaccard; see header TODO) — smoke-test only until Stage 3 swaps in full geff matching.
- Promotion gated on local trusted scorer + cross-fold stability; public LB is diagnostic only.

## Env

- Python 3.13.5 (verified `python3 --version`), **no GPU**, ~113 GB free. No full training on this VM.
- `scripts/` contains: `score.py`, `run_loop.sh`, `new_experiment.sh` (no `run_loop.py` — correct any such reference to `.sh`).

## Auth status (verification commands — re-run, do not assume)

- Kaggle CLI (`~/.local/bin/kaggle`): `~/.kaggle/kaggle.json` EXISTS + `docs/AUTH.md` reports `kaggle competitions list` works, but an earlier scout reported unauthenticated → treat as **UNVERIFIED, blocker stays flagged** until confirmed:
  `export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"`
  then `kaggle competitions download -c biohub-cell-tracking-during-development -p data/` (requires Rules acceptance on competition page first).
- `gh`: **UNAUTHENTICATED (verified 2026-09-09: `gh auth status` → "not logged in")** — cannot create/push `davidlueng986-alt/kaggle-biohub-cell-tracking-rd`. Unblock: `gh auth login` (device-code flow), verify with `gh auth status`.
- Never commit secrets. See `docs/AUTH.md`.

## What exists

- `docs/`: PROTOCOL.md (frozen v1.0), COMPETITION.md, AUTH.md.
- `scripts/`: score.py (simplified), run_loop.sh, new_experiment.sh.
- `experiments/EXP-0000/`: template (hypothesis.md, plan.md, notes.md, metrics.json placeholder); `run_loop.sh --dry-run` validates it. Verified passing 2026-09-09.
- `experiments/EXP-0001/`: dry-run DONE (owner: dryrun-experimenter) — toy fold0/fold1 scores in `metrics.json` (simplified scorer, `dry_run: true`, decision keep-trying); see RESULTS.md row. Do not re-run blindly; coordinate with owner.
- `knowledge/`: this file + HYPOTHESES.md (H-001 active, H-002–H-005 backlog) + RESULTS.md (EXP-0000 template row, EXP-0001 pending).
- No commits/pushes (gh blocked). No real scores yet.

## Current best

None yet (real-data best). EXP-0001 dry-run harness passes on toy data (fold0-toy score 0.600, fold1-toy 0.333, simplified scorer) — not a promotable result. Next promotable target: EXP-0002 real embryo-CV baseline once Kaggle auth + data + full scorer unblock.

## Next loop steps (cold agent — copy/paste)

```bash
cat knowledge/STATE.md knowledge/HYPOTHESES.md knowledge/RESULTS.md
cat docs/PROTOCOL.md docs/COMPETITION.md docs/AUTH.md
ls experiments/
# Auth checks (do first — blockers until they pass):
export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"
gh auth status
# Loop (EXP-0001 owned by dryrun-experimenter — read it, don't recreate):
bash scripts/run_loop.sh --dry-run
# New experiment (only for EXP-0002+):
bash scripts/new_experiment.sh EXP-0002 "<title>"
```
