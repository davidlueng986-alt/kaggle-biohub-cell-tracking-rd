# Task — Auto AI R&D system for Kaggle Biohub Cell Tracking During Development

You are OpenCode on the VM. Model: Muse Spark 1.3 contributor. Use **maximum / xhigh reasoning effort**. Agent: prefer **orchestrator** (`mode: all`) for design→confirm→execute; permission is always-allow.

Project root: `/home/box/workspace/kaggle-biohub-rd` (also `~/workspace/kaggle-biohub-rd`).

## Goal

Research and **build** a durable auto AI R&D workflow system (not a one-off notebook) for the Kaggle competition **Biohub – Cell Tracking During Development** (confirm exact slug/title via Kaggle skill / web).

Loop the system must implement and operate:

1. **提出假設 (Hypothesize)** — grounded in literature, data EDA, prior runs, failure modes
2. **落實成可執行實驗 (Operationalize)** — code + config + seeds + data splits that another agent can run cold
3. **跑 (Execute)** — training / inference / eval pipelines
4. **可信評分器 (Trusted scorer)** — offline metric aligned with competition metric; CV / holdout that **does not overfit public LB**; shake-up resistant design (Grandmaster style)
5. **更新知識 → 下一假設 (Update knowledge)** — write durable artifacts so the next loop (and a different agent with empty chat) can continue

## Anti-overfit / anti-shakeup requirements (non-negotiable)

- Never treat public LB as the optimization target
- Prefer: nested / group-aware CV matching biological structure (embryo/time/condition leakage prevention), trust a frozen local validation protocol
- Track public LB only as a diagnostic; gate promotion on local trusted scorer + sanity checks
- Document known leakage risks for tracking metrics (ID switches, temporal leakage, etc.)
- Ensemble / selection policy that survives private LB shake-up (diversity, stability across folds, not single-seed LB chase)

## Agent-handoff / no-context requirement

Everything must live in the repo so a **new agent with zero chat history** can catch up:

Suggested layout (adjust if better, but keep the spirit):

```
README.md                 # how to run the R&D loop
docs/COMPETITION.md       # metric, data, rules, pitfalls
docs/PROTOCOL.md          # trusted scorer + CV protocol (frozen)
knowledge/STATE.md        # current best understanding (updated each loop)
knowledge/HYPOTHESES.md   # backlog + status
knowledge/RESULTS.md      # ledger of experiments → scores → decisions
experiments/              # one folder per experiment id
  EXP-XXXX/
    hypothesis.md
    plan.md
    run.sh / configs /
    metrics.json
    notes.md
scripts/                  # shared runners + scorer
.github/                  # optional CI smoke
```

Every experiment commit message / PR must link hypothesis id → result → decision.

## GitHub

- Create or use a public/private repo under `davidlueng986-alt` (e.g. `kaggle-biohub-cell-tracking-rd`)
- Push: protocol, knowledge base, experiment artifacts (not huge raw data), progress
- Prefer small frequent commits so other agents can pull mid-flight
- Do **not** commit secrets (Kaggle tokens, API keys). Use env / ignored files.
- If Kaggle API creds missing on this VM, scaffold auth docs and continue with what can be done (competition page research, protocol, scaffolding); flag blocker clearly in STATE.md

## Skills / tools

- Use installed **kaggle** skill under `~/.config/opencode/skills/kaggle`
- `kaggle` CLI at `~/.local/bin/kaggle` (may need auth)
- Always-approve bash/edits already configured — proceed without waiting for permission prompts

## Deliverables (acceptance)

1. Repo on GitHub with the layout above and a working **loop runner** (even if first real train is deferred on auth/GPU)
2. Frozen `docs/PROTOCOL.md` trusted scorer + anti-shakeup validation design
3. At least one full loop artifact: hypothesis → experiment folder → metrics (or dry-run) → knowledge update
4. `knowledge/STATE.md` written so a cold agent can resume in ≤5 minutes of reading
5. Final summary in chat: repo URL, how to run next loop, blockers (auth/GPU/data)

Start by loading the kaggle skill, confirming competition identity, then design the system (orchestrator Phase 1→2 style if using orchestrator), then build and push.
