# Plan — EXP-0033 Calibration-statistic mapping

## Config / seeds

- No RNG (deterministic). Window t20–29 (10 frames), 6 subset samples.
- Frozen detector: sig_small=(1,3,3), sig_large=(1.6,5,5), min_size=50,
  thr_mode=percentile (asserted in calibrate.py; scripts/* untouched).
- Probe pcts {97.5, 99.0}; LOO notch grid [97.5, 98.0, 98.5, 99.0, 99.5].
- GT best-pct assembled (not re-derived): 0113de3b 99.0 / 0b24845f 98.5 /
  0c582fdc 97.5 / 05b6850b 98.5 / 05db0fb1 97.5 / 062c8d37 98.5.

## Steps

1. Cold run: `./experiments/EXP-0033/run.sh` (calls calibrate.py; ~1 min CPU).
2. calibrate.py per sample×frame: one fresh DoG → response stats (a/b),
   raw absolute-level stats (c), probe thresholds+labels (d; @99.0 counts
   for 0113de3b/05b6850b reused from EXP-0008 with thr-equality gate).
3. Fidelity gates: thr-equality vs EXP-0008 on all 20 reused frames (<1e-4);
   1-frame count parity vs scripts/dog_detect.detect @97.5.
4. Aggregate median-over-window → scipy Spearman per stat vs best-pct →
   LOO 1-NN notch error → verdict → metrics.json.
5. Score with `python3 scripts/score.py --dry-run` — N/A (analysis-only, no
   graphs produced; no scorer input).

## Budget

12h T4 budget — estimated <5 min CPU (measured 28.5 s); no GPU, no uploads.
Fresh compute 60 DoG frames + 100 probe labels, cap 120.
