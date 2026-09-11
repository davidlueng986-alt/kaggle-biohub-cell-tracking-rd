# EXP-0060 — Sign-corrected nested binary-brightness rule (HIGH-B→96)

## Hypothesis

EXP-0059 proved a binary frame-mean brightness cut separates the 6 samples
into regimes perfectly (zero interleave) but with INVERTED sign: known-dark
(dim-cell, dense) samples have the HIGHEST frame-means because bright
background/clutter dominates the mean (the EXP-0021 diagnosis). The frozen
EXP-0059 rule (below-median → 96 / above → 99) therefore misassigned every
sample and scored loso_worst 0.161.

H-002 (sign-corrected, pre-registered here BEFORE any new numbers): the rule

- B(S) = mean raw intensity over frames t20–29 (GT-free, same proxy),
- fit-median split computed on fit samples only (nested — LOSO: other 5;
  embryo-nested: fit embryo),
- **B > median (HIGH-B) → pct 96.0; B ≤ median (LOW-B) → pct 99.0**,
- linker gate 7.0 (image-side policy, unchanged),

beats the trusted BTE on all three bars (loso_worst 0.2092 / micro 0.4826 /
nested_worst 0.4193). Predicted LOSO worst ≈ 0.48 (05db0fb1@96) — testable,
not claimed.

## Background

- docs/PROTOCOL.md v1.2 (frozen metric + trusted envelope cv_tag).
- knowledge/RESULTS.md EXP-0059 row; experiments/EXP-0059/notes.md +
  metrics.json (inverted-split evidence, frozen rows reused here).
- knowledge/STATE.md; trusted BTE from EXP-0053 (loso_worst 0.2092 /
  loso_micro 0.4826 / embryo_nested_worst 0.4193).
- Scorer scripts/score.py v1.1.0 (`score_samples` importable).

## Falsification criteria

CANDIDATE bar (ceiling keep-trying rung, NOT a promotion claim): require
loso_worst strictly above 0.2092 AND micro (adjusted-edge) above 0.4826 AND
nested_worst above 0.4193 — all three. Failing any one falsifies the
sign-corrected rule as a BTE challenger → `keep-trying`.
