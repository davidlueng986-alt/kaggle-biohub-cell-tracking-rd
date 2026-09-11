# EXP-0059 — Nested binary-darkness rule (LOSO-validated)

## Hypothesis

There are (at least) TWO detection regimes in this data — dark/dense/dim-cell
tissue vs bright/sparse tissue — and a single GT-free brightness cut separates
them well enough to assign a fixed DoG percentile per regime. Concretely:

- Brightness proxy B(S) = mean raw intensity over frames t20–29 of sample S
  (GT-free; fixed window, no tuning).
- Fit rule: median of B over FIT samples only; dark side (B ≤ median) gets
  pct 96.0, bright side gets pct 99.0. Link gate fixed at 7. No per-sample
  tuning ever; the two levels are frozen a priori (see Levels below).
- Claim: under 6-sample LOSO (fit median on 5, assign the holdout) and under
  embryo-nested CV (fit median on embryo A, apply to embryo B, both
  directions), this rule beats the trusted BTE on all three bars
  (loso_worst > 0.2092 AND loso_micro > 0.4826 AND nested_worst > 0.4193).

## Background

- docs/PROTOCOL.md v1.2 (frozen metric + trusted envelope, cv_tag).
- knowledge/RESULTS.md rows EXP-0021 (per-embryo transfer REJECTED 3/6 —
  levels are sample-specific), EXP-0033 (fine-grained calibration FAILED,
  rho 0.68 < 0.8), EXP-0042 (moments FAILED, rho 0.77 < 0.8),
  EXP-0039/0040 (@96 dark operating point), EXP-0053 (trusted BTE).
- Prior art bounds this rung: fine-grained GT-free ranking failed twice;
  per-embryo levels demoted; threshold descent parked (merging dominates
  below sample optima, EXP-0011/0057); window selection invalid on small
  windows (EXP-0034/0041).

## Levels (frozen a priori)

- HIGH=99.0: bright-tissue optimum. EXP-0008: 44b6_0113de3b @99 recall 1.000,
  adj 0.9382; lowering to 98.5 cost adj (0.9281, pure count cost). Locked
  operating point for reference tissue.
- LOW=96.0: dark-tissue operating point with multi-sample support.
  EXP-0039: 05db0fb1 @96 recall 0.29→0.68, adj 0.209→0.482. EXP-0040: @96
  helps all three dark samples (0c582fdc replicates; 0b24845f adj passes).
  Deeper levels (@95.0 is 05db0fb1's single-sample optimum) are deliberately
  NOT used: that would be per-sample tuning, and EXP-0057 shows merging
  dominates at 94.5. 96.0 stays clear of the merge-dominated regime while
  capturing the dark recall gain.

## Why binary can succeed where ranking failed

EXP-0033/0042 demanded a MONOTONE ranking: one scalar predicting the optimal
level across all 6 samples with rho ≥ 0.8. That needs within-regime ordering
to be meaningful — but 98.5 spans both regimes (non-monotone), and
within-regime scatter (e.g. 0b24845f vs 0c582fdc both dark, different optima)
destroys rank correlation. A binary rule spends 1 bit, not a full ranking:
it needs only ONE cut separating the two regimes and is insensitive to
within-regime ordering noise. If tissue is truly two-regime, even a noisy
brightness proxy recovers the cut while failing the rho ≥ 0.8 bar.

## Falsification criteria

1. REGIME-ORDERING: if B(S) interleaves known-dark {0b24845f, 0c582fdc,
   05db0fb1} with known-bright {0113de3b, 05b6850b, 062c8d37} so that no
   median cut separates them, the binary story is dead on arrival.
2. CV BARS (single deterministic pass): fail if loso_worst ≤ 0.2092 OR
   loso_micro ≤ 0.4826 OR nested_worst ≤ 0.4193 (need all three strictly
   above; no cherry-picking).
3. MECHANISM: if a holdout assigned to its "correct" side still scores at or
   below its BTE-grid value, brightness does not explain the residual —
   record which samples break the story.
4. No part of this hypothesis may be edited after brightness numbers or
   scores are observed; any level/cut change = new experiment id.
