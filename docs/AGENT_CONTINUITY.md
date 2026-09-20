# Agent Continuity — GitHub vs Hugging Face

**Product decision (PM / Alex 2026-09-20):** any AI agent should be able to resume this R&D without tribal knowledge.

## Split

| Surface | What lives there | Why |
|---------|------------------|-----|
| **GitHub** `davidlueng986-alt/kaggle-biohub-cell-tracking-rd` | Competition brief, PROTOCOL, SOPs, code, scripts, notebooks (small), EXP metadata, knowledge ledgers, agent prompts (`PROMPT-*.md`), this doc, README | Clone → read → act. Context stays in git history. |
| **Hugging Face** (dataset + model repos under same org/user) | Train subset zarrs / large `data/`, checkpoints, heavy EXP artifacts, cached detections that are too big for git | Bandwidth + LFS pain. Agents pull on demand. |

## Never commit

- Secrets: `kaggle.json`, `HF_TOKEN`, `.env`, PATs
- Raw `data/` blobs (pointer files / download scripts only)
- `checkpoints/`, large `*.pt` / `*.ckpt`, big zarrs

## HF token (runtime)

- Box path (chmod 600): `/home/box/.secrets/HF_TOKEN`
- Also mirrored for HF hub: `/home/box/.cache/huggingface/token`
- Export for CLI: `export HF_TOKEN="$(cat /home/box/.secrets/HF_TOKEN)"`
- **Never** put the token in README, git, chat logs you commit, or agent prompts that get pushed.

## Target HF repos (create if missing)

1. **Dataset** `davidliang986/biohub-cell-tracking-rd-data` (adjust username after `huggingface-cli whoami`)
   - Contents: per-embryo train subset used by trusted CV; layout documented in `data/README.md` (git) with HF paths.
   - **TODO (D4 2026-09-20):** intended name only — HF unreachable (stored token 401, no `huggingface-cli` on box).
     Do not invent URLs; confirm via whoami, create, then record real paths in root README + `data/HF_MANIFEST.md` (D2-owned).
2. **Models** `davidliang986/biohub-cell-tracking-rd-ckpts`
   - Contents: promoted / reference checkpoints only (tagged by EXP id).

If username differs, rename repos to match whoami and update README table.

## Agent onboarding (minimal)

1. Clone GitHub repo; read `README.md` → `docs/PROTOCOL.md` → `knowledge/STATE.md`.
2. Install `requirements.txt`; place Kaggle + HF credentials locally (not in repo).
3. Fetch data/ckpts per `data/HF_MANIFEST.md` (`huggingface-cli download …` as documented there).
   (`scripts/hf_pull.py` does not exist yet — use the manifest commands until it lands.)
4. Run `python scripts/score.py --dry-run` + `python scripts/trusted_cv.py --smoke` before any EXP.
5. Follow PROTOCOL v1.2 trusted CV; do not trust old 0.8194 / Forge 0.946 as BTE.

## README must advertise

- Competition name + Kaggle slug + what we optimize (trusted CV → Private LB gold)
- GitHub vs HF split (this doc)
- How another agent continues (5 steps above)
- Link to `docs/AUDIT-FIX.md` while repair is active; HALT gold chase until Wave 1 gate
- Auth pointers without secrets
