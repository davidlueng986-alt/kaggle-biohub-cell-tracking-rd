# LEDGER_ADDENDUM — EXP-AUDIT-01 (append to STATE / EXP-AUDIT-00 LEDGER on merge)

- Source: `RESULTS/EXP-AUDIT-01/metrics.json` (one-shot `trusted_cv.py --full`, 2026-09-20).
- Scorer 1.2.0 (S1–S13 oracle-aligned) / PROTOCOL 1.2 / cv_tag trusted / S9 PM-locked
  (div dropped when division-less; 0.5193 = legacy_harness only, never standing).
- Elapsed 2313.2 s; cache = default repo-relative `det_cache/`
  (11 frozen-manifest combos reused, 25 combos x 100 frames detected on demand).
- Standing (official-comparable): loso_micro **0.4825902886**; loso_worst **0.1670288502**
  (moved from stored-count 0.2091686409 under fresh rescore — robustness-only, no gate impact);
  embryo_nested 44b6 micro **0.4192839812** (div NaN) / 6bba micro **0.6135725168** (div 0.0);
  **embryo_nested_worst = 0.4192839812 (official standing 0.4193)** — pre-rerun baseline
  reproduced bit-identically under locked S9.
- Post-run suites: test_score 14/14, test_trusted_cv 4/4 (green).
- Gold R&D remains HALTED; no tuning, no new EXPs, no commit (D1-rebaseline closeout).
