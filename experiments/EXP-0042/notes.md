# Notes — EXP-0042 Higher-moment DoG shape descriptors vs per-video operating level

## Log

- 2026-09-11: `bash experiments/EXP-0042/run.sh` → exit 0, 90.7 s wall.
  20 fresh @98.5 detects (0b24845f + 0c582fdc × t20–29; the only missing
  combos — EXP-0009 covers 0113de3b/05b6850b @98.5, EXP-0021 covers
  05db0fb1/062c8d37 @98.5, all params asserted) + 60 fresh DoG for stats.
- Fresh-det fidelity: per-frame det means reproduce EXP-0024 exactly
  (0b24845f 155.0/f, 0c582fdc 162.3/f, 05db0fb1 285.0/f); recall
  cross-checks pass (0.80 / 0.00 / 0.1888). Fixed-@98.5 recall: 0113de3b
  1.00 (3/3 GT — coarse), 05b6850b 1.00 (84/84), 062c8d37 0.973 (71/73).
- Spec deviation found in probe: DoG p50 < 0 on ALL 60 frames (−1 to −6),
  so r995_50 is negative everywhere (ranking = reverse of p99.5/|p50|;
  |rho| unaffected). Recorded as-measured, not redefined.
- RESULT: best tail24 rho_best=0.7715 (p=0.07), rho_fixed98=0.8117
  (p=0.0499 nominal) but LOO 3/6 → STOP (criterion needs |rho|>=0.8 AND
  LOO>=5/6 jointly; the single rho-bar pass fails LOO badly).

## Decisions

- STOP: higher moments also fail. Do NOT run EXP-0043 self-calibrated
  rule on these grounds; per-video calibration needs GT or a learned
  density estimator — confirms EXP-0033's conclusion at higher order.
- tail24's nominal p=0.0499 is NOT evidence: 7 stats × 2 targets = 14
  tests (multiple-comparison luck favours false GO), fixed-recall target
  is noisy (0113de3b 3 GT nodes; heavy ties), and LOO 3/6 shows no
  predictive value. Sensitivity alt (05db0fb1 best 96.0): tail24
  rho_alt=0.8197, LOO still 3/6 — verdict unchanged.

## Why it failed (load-bearing mechanism)

- Same structural block as EXP-0033 one rung up: skew/kurt cleanly split
  bright-background {0b24845f, 0c582fdc, 05db0fb1} (skew 1.4–1.9) from
  clean {0113de3b, 05b6850b, 062c8d37} (skew 4.6–7.8), but best-pct cuts
  ACROSS the split (0b24845f wants 98.5 with the clean refs; 0113de3b
  wants 99.0 above them). LOO errs [1,2,2,1,2,0]: leaving any sample out,
  its nearest neighbour in tail24-space sits on the wrong notch.
- tail24's fixed-recall signal is real but useless for calibration: tiny
  extreme-tail mass (~1e-4 on 0b24845f/05db0fb1) flags detector-blind
  videos, yet blind videos span best-pcts 97.5 AND 98.5 — the direction
  a self-calibrated rule would need to move is undetermined.

## Caveats

- n=6, heavy ties in best-pct ({97.5×2, 98.5×3, 99.0×1}); 7 stats tested.
- 0113de3b window recall from 3 GT nodes (t20–29 is GT-sparse there);
  062c8d37 best-pct still single-point censored (EXP-0021).
- Otsu computed on the DoG response (not raw intensity) per mission spec;
  a raw-intensity Otsu variant was out of scope.
