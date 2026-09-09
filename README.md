# Kaggle Biohub Cell Tracking During Development — R&D Loop

Auto AI R&D system (hypothesize → operationalize → execute → trusted score → update knowledge).
Target repo: `davidlueng986-alt/kaggle-biohub-cell-tracking-rd`.
Competition: Biohub – Cell Tracking During Development (`biohub-cell-tracking-during-development`, code-competition).

## Setup

```bash
python3 --version  # 3.13 expected; no GPU on current VM
pip install -r requirements.txt  # when added by scaffolder-code
cp kaggle.json ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json  # never commit
```

See `docs/AUTH.md` (protocol-architect) for Kaggle + GitHub auth details.

## Auth (current status: BLOCKED)

- Kaggle CLI (`~/.local/bin/kaggle`): unauthenticated — no `~/.kaggle/kaggle.json`.
- `gh`: unauthenticated — cannot create/push `davidlueng986-alt/kaggle-biohub-cell-tracking-rd` yet.
- Do not embed secrets. Auth blockers also flagged in `knowledge/STATE.md`.

## How to run the R&D loop

One experiment = one folder under `experiments/EXP-XXXX/` (see `experiments/EXP-0000/` template).

```bash
# 1. Pick hypothesis from knowledge/HYPOTHESES.md, scaffold folder
ls experiments/  # next id = max + 1
mkdir -p experiments/EXP-0001 && cp experiments/EXP-0000/*.md experiments/EXP-0001/

# 2. Edit hypothesis.md + plan.md in the new folder

# 3. Dry-run the shared loop runner (no data / no GPU needed)
bash scripts/run_loop.sh --dry-run

# 4. Real run (requires auth + data, GPU recommended)
bash scripts/run_loop.sh
```

Loop runner and scorer live in `scripts/` (`run_loop.sh`, `score.py`) (scaffolder-code). Validation protocol in `docs/PROTOCOL.md` (protocol-architect).

## Promotion rule

An experiment promotes to new best **only if ALL hold**:

1. Improves the frozen trusted scorer on embryo-grouped CV (see `docs/PROTOCOL.md`), not public LB.
2. Stable across folds/seeds (no single-seed or single-embryo win; check division_jaccard separately).
3. Public LB used as diagnostic only; large local↔LB divergence triggers investigation, not promotion.
4. `knowledge/RESULTS.md` + `knowledge/STATE.md` updated with hypothesis id → result → decision.

Metric: `score = adjusted_edge_jaccard + 0.1 * division_jaccard`. Train has 2 embryos only → never split by frame; split by embryo.
