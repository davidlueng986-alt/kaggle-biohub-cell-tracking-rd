# AUDIT-FIX Wave 0 + Wave 1 Stage A — Merge Ledger (Stage B)

- Date (UTC): 2026-09-20
- Merger: orchestrator Stage B (after A1–A4 parallel)
- Gold R&D: HALTED. PM owns direction. Forge 0.946 / 0.8194 NEVER used as targets.
- Gate intent: official fixture diff=0, trusted_cv micro includes +0.1·div, EXP-0053 republished under corrected harness. Wave 2 NOT started.

## Wave 0 — Oracle pin + baseline (shared by A1–A4, re-verified by merger)

- Repo: https://github.com/royerlab/kaggle-cell-tracking-competition @ 075fc5f5a52d11077f9dc2b074644618f26939e2 (main 2026-07-17)
- Package: tracking_cellmot 0.1.0, local /tmp/opencode/official (src/tracking_cellmot/{metrics,division_metrics}.py)
- Backend: tracksdata 0.1.0rc10, scipy 1.18.1, polars 1.44.2, env /tmp/opencode/venv-oracle
- Functions: metrics.evaluate / _evaluate_matched_graph, division_metrics.evaluate_divisions / score_divisions / match_divisions / extract_divisions, metrics.per_sample_metrics / summarise / evaluate_datasets / _jaccard, evaluate._read_estimated_n_total, csv_to_geffs.build_graph_from_rows
- Baseline: repo scripts/score.py diverged on S1–S3 / S4–S7,S11,S12 / S8–S10,S13 as documented per-agent below; each agent froze before/after repros in RESULTS/EXP-AUDIT-00/fixtures/.
- Note: PyPI unreachable from this VM — reuse /tmp/opencode/venv-oracle, do not reinstall.

## A1 Scorer-core S1–S3 — GREEN (scope met)

- Evidence: RESULTS/EXP-AUDIT-00/A1.md, diff_a1.py, diff_report.json, fixtures/a1_*.json ×5
- Claim: 5/5 fixtures pair_diff=0 count_diff=0 + 3000-scene fuzz seed 7, 0 diffs; test_score 14/14 at A1 time.
- Files: scripts/score.py match/filter/dedup only (scipy _match_group_scipy bit-exact + pure-python fallback, _filter_pred_edges dedup/filter/collapse/cap, edge_counts pred_nodes wiring, SCORER 1.1.1); test_score.py fixed wrong_link + added nonconsecutive test.
- Merger re-run note: `diff_a1.py` in merged tree globs all fixtures/* and crashes `KeyError: 'pred'` on non-a1 schemas (pre-existing prefix-filter debt, also noted by A2). A1 scope itself remains GREEN when run on a1_* fixtures; needs 1-line prefix filter (Wave-1 merge follow-up, non-blocking for A1 gate).
- Residuals (A1 documented): matched-first vs lowest-id dedup corner unobserved in fuzz; no-scipy fallback drops phantoms (scipy installed, non-issue).

## A2 Scorer-division S4–S7,S11,S12 — GREEN (scope met)

- Evidence: RESULTS/EXP-AUDIT-00/A2.md, diff_a2.py, diff_report_a2.json, fixtures/a2_*.json ×8
- Merger re-run: 8/8 count_diff=0 pinned=True + fuzz 100 scenes seed 7, 0 diffs, exit 0 (full 500-scene claim in A2.md: 200 seed7 + 300 seed123).
- Fixes: direct-child precedence + unanimous-grandchild fallback (S4), whole-fork poison (S5), GT==2 exactly (S6), considered-FP class (S7), per-window rematch _div_window_match (S11), S12 oracle pin TP1/FP0/FN0.
- Files: scripts/score.py division section only + test_score S12 pin. No regression: A1 fixtures still exact per A2; TestDivision 3/3 OK; --dry-run OK.
- Non-blocking notes: test_tp_fn / test_micro_weight failures are A3-owned (see A3); diff_a1 prefix debt noted.

## A3 Scorer-aggregate S8–S10,S13 — GREEN (scope met, with 2 expected unit-test failures)

- Evidence: RESULTS/EXP-AUDIT-00/A3.md, diff_a3.py, a3_report.json, fixtures/a3_*.json ×5
- Merger re-run: 5/5 [OK] 0 diffs pinned=True, exit 0 (table in A3.md: S8 NaN/NaN/NaN, S9 1.0/NaN/1.0, S10 0.5/NaN/0.5 n_adj2, weights 0.68333… bit-identical, dup_ids TP1/FP0/FN0).
- Fixes: T_true GT-only (S8 exploit 1.1→NaN closed), zero-div drop-term div NaN + warn score=adj (S9 1.1→1.0), edge 0/0→NaN + weight-0 skip + n_adj (S10 0.92→0.5), _expand_duplicate_ids last-occurrence-wins (S13 {0,1,1}→{1,0,0}).
- Files: scripts/score.py aggregate only, SCORER 1.1.1→1.2.0. Did NOT touch trusted_cv/test_score.
- Expected: test_score 12/14 — test_tp_fn + test_micro_weight assert OLD buggy no-T_true behavior (NaN now correct). Wave-1 merge must update them (A3 gives replacements: test_T_true_penalty pattern + a3_weights).
- F6: oracle evaluate() CRASHES on empty/empty + pred-nonempty/gt-empty (official evaluate_pairs SKIPs); repo NaN-skips — same aggregate, graceful; frozen in a3_zero_counts with skip-parity.

## A4 Trusted-CV C1–C6 — GREEN (scope met)

- Evidence: RESULTS/EXP-AUDIT-00/A4.md, A4_corrected_EXP0053.json, A4_smoke_fixed.json
- Merger re-run: test_trusted_cv 4/4 OK.
- Fixes: C1 _composite_micro edge+0.1*div (loso + nested), C2 repo-relative REPO paths, C3 lazy zarr, C4 grid pct=96 process-only (no change), C5 test-gap evidence only, C6 gt_cache=None + N_FRAMES/DEFAULT_FRAMES + provenance (T_true/assign/div/dc/raw/n_det, micro_edge/micro_div).
- Micro check: --smoke loso_micro 0.8238688007 vs edge-only 0.7238688007 delta +0.1000 (audit 0.7239/0.8239 to 4dp). grep home/box empty; frozen hits work with zarr blocked.
- EXP-0053 recalc (stored v1.1.0 counts, no rescore, HPs unchanged): loso_micro 0.4825902886 unchanged (div 0.0), loso_worst 0.2091686409 unchanged, embryo_nested.44b6 0.4192839812→0.5192839812 (div 1.0), 6bba 0.6135725168 unchanged (div 0.0), embryo_nested_worst 0.4193→0.5193.

## CRITICAL PM BLOCKER — S9 vs C1 convention (A3 F5 vs A4)

- A3 (code-proven): official summarise on division-less split returns division NaN, score=adj (its own test asserts this). Hence 0.5193 is NOT official-comparable; official-comparable 44b6-fold stays 0.4193 div NaN.
- A4 (old-harness convention): 0.5193 = 0.41928…+0.1 follows audit C1 headline, not oracle S9 rule.
- A3 H1: trusted_cv `_composite_micro`/`fit_best` still hard-encodes w==0→1 + micro_div=1.0 if dden==0, mirroring OLD scorer; diverges from fixed score.py + oracle on division-less folds; NaN-edge poison risk if GT lacks T_true.
- Decision needed (N1): recommend oracle (S9 drop-term; publish 0.4193 div-NaN as official-comparable) OR explicitly label 0.5193 as old-convention-composite. B1 must NOT republish 0.5193 as official until ruled. Wave-1 gate C1/S9 needs one convention.

## Merged-tree verification (orchestrator, 2026-09-20)

- diff_a2: 8/8 OK + fuzz 100/0, exit 0 — PASS
- diff_a3: 5/5 OK pinned, exit 0 — PASS
- diff_a1: crashes on non-a1 fixtures (KeyError pred) — SCOPE PASS but harness needs prefix filter fix
- test_trusted_cv: 4/4 OK — PASS
- test_score (unittest): 12/14 — 2 FAILS EXPECTED (test_tp_fn, test_micro_weight assert pre-fix behavior; see A3)
- score.py --dry-run: claimed green by A1/A2/A3 (merger did not re-run full; see commit)
- No Forge scores used. Gold HALTED throughout. No push.

## Files in this commit

- scripts/score.py (A1 core + A2 division + A3 aggregate, SCORER 1.2.0)
- scripts/test_score.py (A1 link tests + A2 S12 pin; 2 A3-owned updates pending)
- scripts/trusted_cv.py (A4 C1/C2/C3/C6)
- RESULTS/EXP-AUDIT-00/{A1.md,A2.md,A3.md,A4.md,diff_a1.py,diff_a2.py,diff_a3.py,diff_report.json,diff_report_a2.json,a3_report.json,A4_corrected_EXP0053.json,A4_smoke_fixed.json,fixtures/a1_*,a2_*,a3_*}
- .gitignore secrets hunk (pre-existing, kept)
- This LEDGER.md

## Gate verdict

- Official fixture diffs: A2 0, A3 0, A1 0 on owned fixtures (with harness-filter debt) — CONDITIONAL PASS
- trusted_cv micro +0.1·div + portable + no hardcode — PASS (subject to H1 follow-up)
- EXP-0053 corrected numbers published as recalc — DONE but BLOCKED on S9-vs-C1 ruling before B1 retag / Wave-2 entry
- Wave 2 (B1 tags L*, B2 skeleton N1–N2, B3 detect/link P*): DO NOT ENTER until PM rules N1 + test_score 2 updates + diff_a1 prefix fix landed.

## Next for PM

1. Rule N1 (S9 drop vs C1 +0.1): oracle 0.4193 div-NaN or old-convention 0.5193?
2. Approve Wave-1 merge follow-ups: diff_a1 prefix filter, test_tp_fn/test_micro_weight updates, A4 H1 (w==0/NaN/div-NaN alignment).
3. Confirm merger commit SHA below, then authorize Wave 2 scope.
