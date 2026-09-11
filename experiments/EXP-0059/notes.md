# Notes — EXP-0059 Nested binary-darkness rule (LOSO-validated)

## Log

- Scaffolded via scripts/new_experiment.sh (EXP-0059 was free).
- hypothesis.md + plan.md written BEFORE any new numbers (levels 96.0/99.0
  frozen, median-split rule, gate 7).
- Brightness B(S) = frame-mean t20–29: 062c8d37 62.0 / 05b6850b 85.9 /
  0113de3b 256.3 / 0c582fdc 626.7 / 05db0fb1 1002.5 / 0b24845f 1009.1.
  REGIME SPLIT IS PERFECT (no interleave) BUT SIGN-INVERTED vs the prior:
  known-dark samples have the HIGHEST means (bright clutter dominates the
  mean — exactly the EXP-0021 diagnosis), known-bright the lowest.
- Frozen rule (below-median → 96) therefore misassigns EVERY sample:
  dark-needing tissue gets 99, bright tissue gets 96.
- Cap decision (recorded before linking/scoring): rule needs 4 missing
  combos × 100f = 400 > 300 cap → omitted 44b6_0113de3b@96 (bright
  reference, recall-saturated; cannot rescue the worst bar). Fresh exactly
  300f: 05b6850b@96, 062c8d37@96, 05db0fb1@99 (dog_detect.main in-process,
  exact CLI path/defaults).
- link (BL.link gate 7, gid reassignment) + score (score_samples v1.1.0;
  EXP-local scipy swap, equivalence gate PASS: 0113de3b@99 ec 47/2/3
  identical both backends; scripts/* untouched).
- Frozen rescore sanity: 0b24845f@99 edge 0.1040 / 0c582fdc@99 edge 0.0958
  reproduce EXP-0021 ledger; 062c8d37@96 edge 0.7860 reproduces EXP-0043.

## Results (PROTOCOL v1.2, scorer v1.1.0, cv_tag trusted)

- LOSO (5/6 scored): 0b24845f@99 score 0.2040; 0c582fdc@99 0.1958;
  05b6850b@96 0.5989; 05db0fb1@99 0.1610; 062c8d37@96 0.7860.
  Partial worst = 0.1610 (< BTE 0.2092; settled — unscored 0113de3b@96 can
  only lower it). Partial micro_edge = 0.4330 (< BTE 0.4826; bound: adding
  0113de3b@96 at even edge 1.0 gives ≤ 0.447, still sub-BTE).
- Nested COMPLETE both arms: fit-44b6→6bba micro 0.4470; fit-6bba→44b6
  micro 0.3415; nested_worst = 0.3415 (< BTE 0.4193).
- Bars: 0/3 → PROMOTION-CANDIDATE bar FAILED. No cherry-picking involved.

## Decisions

- `keep-trying` — directional rule FALSIFIED (sign inverted). Mechanism:
  frame-mean intensity is dominated by bright background/clutter, so
  HIGH-mean samples are exactly the dim-cell samples needing LOW pct.
  No sample breaks the BINARY story (split separates 3v3 perfectly with
  zero interleave); ALL samples break the DIRECTIONAL story.
- Why this still advances the program: EXP-0033/0042 proved no monotone
  scalar reaches rho 0.8; here a 1-bit cut separates the regimes cleanly.
  The failure is sign-only, i.e. a one-line, pre-specifiable correction.
- Next-stage input (NEW experiment id — sign flip is a cut change, barred
  here by pre-registration): sign-corrected rule HIGH-B → 96.0 / LOW-B →
  99.0. Under it, LOSO+nested needs only ONE fresh combo (062c8d37@99,
  100f): all dark-side assignments (0b24845f/0c582fdc/05db0fb1@96) and
  bright-side 0113de3b/05b6850b@99 are frozen. Predicted LOSO from frozen
  rows: worst ≈ 0.48 (05db0fb1@96) vs BTE 0.2092 — testable, not claimed.
- Scope compliance: created under experiments/EXP-0059/ only; no
  scripts/docs/knowledge/other-experiment/data edits; no pip; no kaggle;
  no commits; 300/300 fresh-frame budget; no secrets.
