# EXP-AUDIT-01 — One-Shot Audit-Closure Rerun (D1-rebaseline)

- Date (UTC): 2026-09-20 (start 17:11:08Z, end ~17:49:40Z)
- Owner: D1-rebaseline (AUDIT-FIX closeout, one-shot; Gold HALTED, no tuning, no Wave 4)
- Command (exact, default grid + default repo-relative cache):
  `python3 scripts/trusted_cv.py --full --out RESULTS/EXP-AUDIT-01/metrics.json`
- Grid: DoG pct {96, 97, 98, 98.5, 99, 99.5} x link gate {7, 10} (12 cfgs x 6 samples = 72 link+score runs)
- Versions: `protocol_version` 1.2, `scorer_version` 1.2.0 (S1–S13 fixed), `cv_tag` trusted
- S9 LOCK honored: division-less splits DROP the +0.1 div term (div NaN); 0.5193-style
  legacy_harness +0.1 is NOT cited as standing.
- Elapsed: `elapsed_s` 2313.2 s (~38.6 min, single process, 8-core box)
- Cache: repo-relative `det_cache/` (default). 11/36 (sid,pct) combos reused frozen
  manifest artifacts (EXP-0008/0009/0021/0039/0040); 25 combos x 100 frames = 2500 det
  files detected on demand into `det_cache/` during this run.
- S9 drop-term evidence: run.log line 1 — official scorer UserWarning
  ("No divisions present across any sample in this split; dropping division term")
  fired during the rerun, confirming the locked code path was active.

## Official-comparable standing lines (locked S9)

| Line | Value (full precision) | 4dp |
|------|------------------------|-----|
| loso_micro | 0.4825902885914996 | 0.4826 |
| loso_worst | 0.1670288501535372 (holdout 44b6_0c582fdc @ HP 97.0/7.0) | 0.1670 |
| embryo_nested 44b6 micro (= micro_edge, micro_div NaN) | 0.4192839811593832 | **0.4193** |
| embryo_nested 6bba micro (= micro_edge, micro_div 0.0) | 0.6135725168230305 | 0.6136 |
| **embryo_nested_worst (official standing)** | **0.4192839811593832** | **0.4193** |

Fitted HPs — nested: 44b6 <- (97.0, 7.0), 6bba <- (97.0, 7.0). LOSO holdouts: all
(97.0, 7.0) except 6bba_05b6850b <- (96.0, 7.0), 6bba_05db0fb1 <- (98.5, 7.0).

## Delta vs pre-rerun (EXP-AUDIT-00 ledger, stored-count recalc)

- embryo_nested 44b6: 0.4192839812 -> 0.4192839812 — BIT-IDENTICAL, S9 lock baseline confirmed.
- embryo_nested 6bba: 0.6135725168 -> 0.6135725168 — identical.
- embryo_nested_worst: 0.4193 official (0.5193 remains legacy_harness only, not reproduced here).
- loso_micro: 0.4825902886 -> 0.4825902886 — identical to 10dp.
- loso_worst: 0.2091686409 -> 0.1670288502 — MOVED under fresh rescore. The old min
  (6bba_05db0fb1 @ 98.5/7.0 = 0.2091686409) rescores bit-identically here, but holdout
  44b6_0c582fdc now fits HP (97.0, 7.0) and scores 0.1670288502, becoming the new min.
  LOSO is robustness-only (L6: embryo_nested is the promotion gate), so no gate impact.

## Per-embryo micro detail (official-comparable)

- 44b6 fold: per-sample scores 0.9004 / 0.3254 / 0.1670, all div NaN (dc 0/0/0);
  fold micro_div NaN -> div term dropped (S9). micro = micro_edge = 0.4192839812.
- 6bba fold: per-sample 0.6879 (div NaN) / 0.3942 (div 0.0, dc 0/0/3) / 0.8606
  (div 0.0, dc 0/0/1); fold micro_div 0.0 (divisions exist, term kept, adds 0.0).
  micro = micro_edge = 0.6135725168.

## Verification (post-run, time permitting — done)

- `python3 scripts/test_score.py` — 14/14 OK
- `python3 scripts/test_trusted_cv.py` — 4/4 OK

## Files

- `metrics.json` — full trusted-CV output (this run)
- `run.log` — streaming stdout/stderr of the one-shot run (72 [cache] + 6 [loso] + 2 [nested] lines)
- `README.md` — this file
- `LEDGER_ADDENDUM.md` — LEDGER_ADDENDUM section (standing numbers for STATE merge)
- (sibling) `D4.md` — D4-continuity evidence, not mine, left untouched.

No code, tags, docs, or commits touched. No new gold EXPs.
