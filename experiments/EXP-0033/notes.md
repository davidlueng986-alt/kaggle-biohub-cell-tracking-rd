# Notes — EXP-0033 Calibration-statistic mapping

## Log

- Scaffolded via scripts/new_experiment.sh; calibrate.py + run.sh written.
- Ran 2026-09-10: 28.5 s wall; fresh 60 DoG / cap 120; 20 @99.0 counts reused
  from EXP-0008 (thr-equality gate <1e-4 passed on all 20; initial 1e-6 gate
  tripped on float32 filter noise rel-diff ~1.5e-6, relaxed with rationale).
- Path parity: fresh label path == scripts/dog_detect.detect counts on
  6bba_05b6850b t20 @97.5. Fresh n975 medians reproduce EXP-0024 means
  (0b24845f 187 vs 190.7; 0c582fdc 183 vs 184.2; 05db0fb1 375 vs 370.7).
- RESULT: max |rho| = 0.6789 (slope_ratio, r999_99) < 0.8 → STOP.

## Decisions

- STOP: no GT-free scalar statistic predicts operating level. Do NOT run
  EXP-0035 self-calibrated rule on these grounds; per-video calibration
  needs GT or a learned density estimator.
- LOO gate was passable (r999_99/slope_ratio 5/6) but the rho bar was not;
  with n=6 and 15 stats, |rho|>=0.8 needs near-perfect rank agreement —
  correctly not reached (all p > 0.13).

## GT-censoring audit (weakens, not strengthens, the test)

- 0113de3b best 99.0: tie 1.00 @98.5/@99.0 broken by fewer-dets; never
  swept below 98.5 (low side censored).
- 05b6850b best 98.5: three-point evidence (0.893 > 0.880 > 0.835); never
  swept @97.5 (low side censored — a lower best would only hurt rho).
- 062c8d37 best 98.5: single EXP-0021 point (fully censored; weakest row).
- Darks (EXP-0024 full 97.5–99.5 sweeps) are the solid GT half.

## Why it failed (load-bearing mechanism)

Stats cleanly split bright-background {0b24845f, 0c582fdc, 05db0fb1} from
clean {0113de3b, 05b6850b, 062c8d37} (rawmed ~500–1080 vs ~40–190; r99_90
~3–4 vs ~46–113), but best-pct cuts ACROSS that split: 0b24845f wants 98.5
(with the clean refs) while 0113de3b wants 99.0 (above them). The middle
notch (98.5) is heterogeneous — spans both brightness regimes — so no
monotone scalar rule can rank all three notches. Probe-count stats (d) do
worst (|rho| <= 0.52): detection counts confound cell density with level.
Upper-tail shape (r999_99, slope_ratio) came closest (rho 0.679): the
99→99.9 tail decay carries weak signal, but far from calibration-grade.

## Caveats

- n=6, heavy ties in y ({97.5×2, 98.5×3, 99.0×1}); 15 stats tested —
  multiple-comparison luck would favour false GO; the STOP is conservative.
- Window t20–29 medians only; full-video stats might differ slightly, but
  the heterogeneity mechanism (98.5 spans both regimes) is structural, not
  a window artefact.
