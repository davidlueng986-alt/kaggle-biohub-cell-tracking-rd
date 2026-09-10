# EXP-0033 — Calibration-statistic mapping

## Hypothesis

A GT-free per-video statistic computed on window frames t20–29 predicts the
sample's best DoG operating percentile (best-pct-by-recall) well enough to
self-calibrate detection without GT: specifically, some candidate statistic
reaches |Spearman rho| >= 0.8 vs best-pct across the 6 subset samples AND
leave-one-sample-out 1-NN prediction lands within one pct-notch for >= 5/6
samples. Pass → GO (recommend EXP-0035 full-video self-calibrated rule);
fail → STOP (per-video calibration needs GT or a learned density estimator).

## Background

- docs/PROTOCOL.md FROZEN v1.1 (score = adjusted_edge_jaccard +
  0.1*division_jaccard; embryo-grouped CV; LB diagnostic only).
- EXP-0021: fixed per-embryo DoG levels do not transfer (refs hold at
  1.000/0.893; dark samples best only 0.80/0.50/0.41 at lower pcts).
- EXP-0024: pct sweep on 3 dark samples — bests 0b24845f@98.5/0.80,
  0c582fdc@97.5/0.50, 05db0fb1@97.5/0.41; "bright clutter owns the tail".
- Refs: 0113de3b@99.0/1.00, 05b6850b@98.5/0.893, 062c8d37@98.5/0.93
  (EXP-0008/0009/0011/0021; partly censored — see notes.md).

## Falsification criteria

max |rho| < 0.8 over all 15 candidate stats, or LOO-within-one-notch < 5/6
for every stat meeting the rho bar → hypothesis REJECTED (STOP).
