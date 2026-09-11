# EXP-0042 — Higher-moment DoG shape descriptors vs per-video operating level

## Hypothesis

First-moment/tail-slope statistics of the DoG response distribution fail to
predict per-video operating level (EXP-0033 STOP, best |rho| 0.68 < 0.8), but
that rung never tested HIGHER-moment shape descriptors. Predicts: at least
one of (a) skewness, (b) excess kurtosis, (c) level-free tail mass above
median+k*MAD (k=6,12,24 — fraction version of EXP-0022's failed absolute
MAD rule), (d) p99.5/p50 ratio, (e) bright fraction above the Otsu threshold
of the DoG response ranks the 6 subset samples' operating level
(fixed-@98.5 window recall and/or assembled best-pct) with |rho| >= 0.8 AND
LOO 1-NN within-one-notch on >= 5/6. GO routes to an EXP-0043
self-calibrated percentile rule (recommended, not run here); else STOP —
higher moments also fail, and per-video calibration needs a learned density
estimator, confirming EXP-0033's conclusion at higher order.

## Falsification criteria

- REJECT higher-moment calibration if NO candidate statistic reaches
  |Spearman rho| >= 0.8 (vs fixed-@98.5 recall or vs best-pct) together with
  LOO within-one-notch >= 5/6 → STOP verdict recorded in metrics.json.
- REJECT the measurement itself if fidelity gates fail (sigma drift,
  reused-det pct/min_size mismatch, recall cross-checks vs EXP-0024 miss by
  more than GT-tie tolerance, fresh-frame cap breach).
