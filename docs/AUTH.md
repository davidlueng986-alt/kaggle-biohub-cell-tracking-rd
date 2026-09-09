# Auth Setup — Kaggle + GitHub

> **No secrets in the repo. Ever.** Tokens, `kaggle.json`, and PATs live in home-directory files or env vars only. Never `git add` them; never paste them into docs, code, or chat logs.

## Kaggle

**Observed state (2026-09-09, this VM): `~/.kaggle/` already contains `kaggle.json` and `kaggle competitions list` works** — auth appears functional. Verify with the check below; skip to step 4 if it passes.

1. **Log in (interactive, preferred):**
   ```bash
   kaggle auth login
   ```
   This stores credentials under `~/.kaggle/` with correct permissions.
2. **Alternative (API token):** Kaggle account → profile photo → Settings → API → *Create New Token* → downloads `kaggle.json`. Then:
   ```bash
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
   chmod 600 ~/.kaggle/kaggle.json
   ```
3. **Accept competition rules** (required before download — the API returns 403 until accepted): open https://www.kaggle.com/competitions/biohub-cell-tracking-during-development → *Rules* → *I Understand and Accept*. CLI download cannot bypass this.
4. **Verify + download:**
   ```bash
   kaggle competitions list --search "biohub"
   kaggle competitions download -c biohub-cell-tracking-during-development -p data/
   ```
5. CLI path on this VM is `~/.local/bin/kaggle`; ensure it is on `PATH` (`export PATH="$HOME/.local/bin:$PATH"`).

## GitHub (`gh`)

**Observed state (2026-09-09, this VM): `gh auth status` → not logged in.** Required before Stage-4 push.

1. **Log in (interactive):**
   ```bash
   gh auth login
   ```
   Choose GitHub.com → HTTPS → login with browser code (recommended on a headless VM: use the device-code flow and approve in your browser).
2. **Verify:**
   ```bash
   gh auth status
   ```
3. **Target repo:** `davidlueng986-alt/kaggle-biohub-cell-tracking-rd` (create if missing: `gh repo create davidlueng986-alt/kaggle-biohub-cell-tracking-rd --private --clone` or via the web UI).
4. Prefer HTTPS + credential helper (set up by `gh auth login`); do not place PATs in repo files or shell history — use `gh auth login --with-token` with the token piped from a file, then delete the file.

## Hygiene

- `git status` before every commit; ensure `~/.kaggle/`, `data/`, `*.json` tokens, and `.env` are git-ignored (scaffolder owns `.gitignore` — confirm it covers these).
- If a secret is ever committed: rotate it immediately (Kaggle: revoke token; GitHub: revoke PAT), then purge from history — do not just delete the file.
