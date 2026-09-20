# AUDIT-FIX — Biohub Cell-Tracking (Alex authorize 2026-09-20)

**Source of truth:** `docs/audits/Biohub_Cell-Tracking_Auto-RD_Merged_Audit_Report.md` (Alex original)
**Owner:** AI Master (OpenCode Orchestrator, Stage A multi-agent parallel)
**Product authority:** PM — do not invent direction; execute this checklist
**R&D loop status:** HALTED until Wave 1 acceptance passes (no new gold EXP chase until scorer+trusted CV honest)
**S9 lock (PM 2026-09-20):** official standing `embryo_nested_worst` = **0.4193** (div NaN, drop-term); **0.5193** = legacy_harness only — never cite as standing / promotion baseline.
**Deadlines (I6, competition page authoritative):** merger/new-entrant deadline **2026-09-22**; final deadline 2026-09-29 23:59 UTC; submission cap 5/day.

## Product decisions (locked)

1. Repair priority: Scorer alignment → Trusted CV harness → Tag honesty → Submission chain → Pipeline scripts → Infra/CI
2. Primary promotion gate after fix: `embryo_nested_*` (trusted); LOSO for robustness only
3. Classical DoG may graduate to fallback after Wave 1 rebaseline — Wave 4 decision, not Wave 1
4. Report concrete trusted CV numbers to Alex (never jargon-only)
5. OpenCode: web UI + `orchestrator` agent mode (not build/API-only) for Stage A parallel

## Wave 0 — Setup (before code)

- [ ] Pin official scorer path/version (`tracking_cellmot`) as differential oracle
- [ ] Create `EXP-AUDIT-00` baseline diff report (repo score.py vs official on fixed fixtures)
- [ ] Acceptance = every audit ID below checked off with repro evidence in RESULTS / PR

## Wave 1 — P0 parallel (4 OpenCode agents)

| Agent | Scope | Audit IDs | Done when |
|-------|--------|-----------|-----------|
| A1 Scorer-core | `scripts/score.py` match/filter/dedup | S1, S2, S3 | Diff vs official = 0 on pairing+edge fixtures |
| A2 Scorer-division | division/fork rules | S4–S7, S11, S12 | Division fixtures match official |
| A3 Scorer-aggregate | T_true / zero-div / weights | S8, S9, S10, S13 | Aggregate fixtures match official |
| A4 Trusted-CV | `scripts/trusted_cv.py` | C1–C6 | Micro includes +0.1·div only when divisions exist (S9 drop-term, PM-locked); no hardcode; portable; EXP-0053 official standing `embryo_nested_worst` = **0.4193** (0.5193 = legacy_harness only, NOT standing) |

**Gate:** all A1–A4 green + EXP-0053 numbers republished under corrected harness before Wave 2.

## Wave 2 — Honesty + submit chain (parallel)

| Agent | Scope | IDs |
|-------|--------|-----|
| B1 Tags | RESULTS/STATE ledger honesty | L1–L6 |
| B2 Submit skeleton | `submission_skeleton.ipynb` | N1, N2 (+ N3–N6 if blocking) |
| B3 Detect/link | dog_detect / gap_link / baseline | P1–P5 as needed |

## Wave 3 — Infra/CI

- I3 smoke.yml: pip install + `trusted_cv --smoke` + official-diff tests
- I1/I7 download_subset + Kaggle auth
- I4 STATE hygiene · I5 requirements · I6 merger deadline 2026-09-22 docs

## Wave 4 — Product (ask PM before acting)

- Graduate Classical DoG? Expand train envelope? Loosen causality? Stricter EXP-0061 bar?

## Execution standard

- Repo: `~/workspace/kaggle-biohub-rd` (or current Biohub gold checkout)
- OpenCode web + Orchestrator; Stage A fan-out A1–A4 in parallel
- Commit/PR per wave; never invent product direction
- Final / blockers → PM; working state → Alex chat directly
- Do NOT reopen continuous gold R&D chase until Wave 1 gate passes unless Alex/PM un-halts

## Out of scope this ticket

- New public LB spam for medal chase
- Trusting Forge 0.946 / old 0.8194 as BTE
