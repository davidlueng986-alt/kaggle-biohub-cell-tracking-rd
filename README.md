# Kaggle Biohub Cell Tracking During Development — R&D Loop

Auto AI R&D system (hypothesize → operationalize → execute → trusted score → update knowledge).
Target repo: `davidlueng986-alt/kaggle-biohub-cell-tracking-rd`.
Competition: Biohub – Cell Tracking During Development (`biohub-cell-tracking-during-development`, code-competition).

## Setup

```bash
python3 --version  # 3.13 expected; no GPU on current VM
pip install -r requirements.txt  # numpy>=2.0 only; no torch/scipy
cp kaggle.json ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json  # never commit secrets
```

See `docs/AUTH.md` (protocol-architect) for Kaggle + GitHub auth details.

## Auth (current status: PARTIAL — Kaggle WORKS, gh BLOCKED; verified 2026-09-09)

- Kaggle CLI (`~/.local/bin/kaggle`): **WORKS** — `~/.kaggle/kaggle.json` present and
  `kaggle competitions list --search "biohub"` returns the competition (verified 2026-09-09).
  Verify: `export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"`.
  Download still requires Rules acceptance on the competition page first.
- `gh`: **BLOCKED** — unauthenticated (`gh auth status` → "not logged in", verified 2026-09-09);
  cannot create/push `davidlueng986-alt/kaggle-biohub-cell-tracking-rd` yet. Unblock: `gh auth login`, verify with `gh auth status`.
- Do not embed secrets. Never commit `kaggle.json`, `.env`, PATs, or `data/`. Auth details in `docs/AUTH.md` and `knowledge/STATE.md`.

## How to run the R&D loop

One experiment = one folder under `experiments/EXP-XXXX/` (see `experiments/EXP-0000/` template).

```bash
# 1. Pick hypothesis from knowledge/HYPOTHESES.md, scaffold folder
ls experiments/  # next id = max + 1
mkdir -p experiments/EXP-0001 && cp experiments/EXP-0000/*.md experiments/EXP-0001/

# 2. Edit hypothesis.md + plan.md in the new folder

# 3. Dry-run the shared loop runner (no data / no GPU needed)
bash scripts/run_loop.sh --dry-run

# 3b. Scorer smoke checks (no data needed)
python3 scripts/score.py --dry-run
test -f scripts/test_score.py && python3 scripts/test_score.py || echo "test_score.py not present yet — skipping"

# 4. Real run (Kaggle auth OK; data download needs Rules acceptance, GPU recommended)
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

## GitHub vs Hugging Face — where things live (D4 continuity)

| Surface | What lives there |
|---------|------------------|
| **GitHub** `davidlueng986-alt/kaggle-biohub-cell-tracking-rd` (this repo) | Competition brief, PROTOCOL, SOPs, code/scripts, small notebooks, EXP metadata, knowledge ledgers, agent prompts, docs |
| **Hugging Face** dataset + checkpoint repos (intended, see below) | Large `data/` blobs, per-embryo train subsets, promoted checkpoints, heavy EXP artifacts |

**Never in git:** secrets (`kaggle.json`, `HF_TOKEN`, `.env`, PATs), raw `data/` blobs, `checkpoints/`, large `*.pt` / `*.ckpt` / zarrs. Pointer docs only (`data/README.md`, `data/HF_MANIFEST.md` — owned by D2, do not edit here).

**Fetch (after HF repos land):** pull commands live in `data/HF_MANIFEST.md` (`huggingface-cli download …`,
`HF_TOKEN` from `/home/box/.secrets/HF_TOKEN` in memory only — never commit, never echo into evidence).

**Intended HF repos (TODO — not yet created; HF unreachable 2026-09-20, stored token returns 401;
confirm username via `huggingface-cli whoami` before creating, do not invent URLs):**

- dataset: `<user>/biohub-cell-tracking-rd-data` — per-embryo train subset used by trusted CV
- checkpoints: `<user>/biohub-cell-tracking-rd-ckpts` — promoted / reference checkpoints only (tagged by EXP id)

## Pins & locks (AUDIT-FIX closeout)

- **Oracle pin:** `tracking_cellmot` (`royerlab/kaggle-cell-tracking-competition`) @
  `075fc5f5a52d11077f9dc2b074644618f26939e2` — differential oracle for scorer alignment (see `RESULTS/EXP-AUDIT-00/`).
- **S9 lock (PM 2026-09-20):** official standing `embryo_nested_worst` = **0.4193** (div NaN, drop-term);
  **0.5193** = legacy_harness only — never cite as standing / promotion baseline.
- **Gold HALTED:** R&D loop HALTED until Wave 1 acceptance passes — no new gold EXP chase until scorer +
  trusted CV honest. Details: `docs/AUDIT-FIX.md`.

## Agent onboarding (5 steps)

1. Read `README.md` → `docs/AGENT_CONTINUITY.md` → `docs/PROTOCOL.md` → `knowledge/STATE.md` → `docs/AUDIT-FIX.md` (while repair active).
2. Install `requirements.txt`; place Kaggle + HF credentials locally (never in repo).
3. Fetch data/ckpts per `data/HF_MANIFEST.md`.
4. Run `python3 scripts/score.py --dry-run` + `python3 scripts/trusted_cv.py --smoke` before any EXP.
5. Follow PROTOCOL trusted CV; do not trust old 0.8194 / Forge 0.946 as BTE.
