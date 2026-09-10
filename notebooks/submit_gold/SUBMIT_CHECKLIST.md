# SUBMIT_CHECKLIST — Gold v7 gate-7 stack (post-reset)

Scope: kernel `liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10`,
kernel version **7** (remote verified: GATE_UM = 7.0 ×1, no 10.0, status COMPLETE).
Pre-reset state (2026-09-10): slots remaining 0; LB refs 56143782/803/804 (v5 gate-10,
all 0.650), 56147475 (v6 gate-10 vectorized, 0.650 diagnostic). No new scores.

**Naming caveat:** kernel id/title still say "gate-10" but v7 code is gate-7.
Do NOT rename/push to fix — use the submit message to disambiguate.

## Post-reset submit sequence (run in this order)

1. Kernel freshness check (read-only):
   `kaggle kernels status liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10`
   Expect `KernelWorkerStatus.COMPLETE`. If code changed since v7 ran, push a new
   version first and wait for COMPLETE — never submit a stale version.

2. Slot check FIRST (standing rule — read-only):
   `kaggle competitions submissions -c biohub-cell-tracking-during-development`
   If output shows a remaining-count line, that command already returned
   success information → **STOP, do not submit** (duplicate-submit burns slots).

3. Confirm slots:
   `kaggle competitions submission-limits -c biohub-cell-tracking-during-development`
   Proceed only if remaining today ≥ 1.

4. Submit kernel version 7 output:
   `kaggle competitions submit -c biohub-cell-tracking-during-development -k liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10 -f submission.csv -v 7 -m "Gold v7: per-embryo DoG + gate-7 links, no forks (diagnostic LB)"`

5. Verify (read-only):
   `kaggle competitions submissions -c biohub-cell-tracking-during-development`
   Confirm the new row appears as COMPLETE and record its ref.

6. Record the returned **publicScore as diagnostic only** in
   `knowledge/RESULTS.md` + `STATE.md` (gate-7 vs gate-10 arbitration;
   prior gate-10 refs all scored 0.650).

## STOP rules

- **Remaining-count output = success → STOP.** Never resubmit after seeing it.
- **Never submit without a COMPLETE fresh version** if code changed since the
  last kernel run — push, wait for COMPLETE, then submit that version number.
- **One submit per decision.** This checklist covers v7 gate-7 only; any further
  submit needs a new decision, not a re-run of this sheet.
- Never print or paste API secrets; Kaggle CLI auth only.
