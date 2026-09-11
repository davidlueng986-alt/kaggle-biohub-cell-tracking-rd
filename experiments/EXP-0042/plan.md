# Plan — EXP-0042 Higher-moment DoG shape descriptors

## Config / seeds

- No RNG (deterministic). Window t20–29 (10 frames), 6 subset samples.
- Frozen detector: sig_small=(1,3,3), sig_large=(1.6,5,5), min_size=50,
  thr_mode=percentile (asserted in moments.py; scripts/* untouched).
- Candidate stats (per-frame, median-over-window): skew, kurt_x (excess
  kurtosis), tail6/12/24 = frac(DoG > median+k*MAD), r995_50 = p99.5/p50,
  otsu_frac = frac(DoG > Otsu threshold of DoG histogram, 256 bins).
- Targets: fixed-@98.5 window recall (reused dets + 20 fresh) AND
  assembled best-pct (EXP-0033 assembly: 0113de3b 99.0 / 0b24845f 98.5 /
  0c582fdc 97.5 / 05b6850b 98.5 / 05db0fb1 97.5 / 062c8d37 98.5).
- LOO: 1-NN in stat space vs best-pct on notch grid [97.5, 98, 98.5, 99, 99.5].

## Steps

1. Cold run: `./experiments/EXP-0042/run.sh` (20 fresh @98.5 detects for
   44b6_0b24845f + 44b6_0c582fdc t20–29, then moments.py; ~2 min CPU).
2. Reuse (asserted, not recomputed): EXP-0009 full_*_t20-29 @98.5
   (0113de3b, 05b6850b) + EXP-0021 full_*_t20-29 @98.5 (05db0fb1, 062c8d37).
3. moments.py: one fresh DoG per sample×frame (60) → all stats from the
   cached array; window recall via score.match_nodes; Spearman vs both
   targets + LOO notch error + sensitivity (05db0fb1 best 96.0) → verdict.
4. Fidelity gates: sigma asserts; reused-det pct/min_size asserts;
   recall cross-checks (05db0fb1≈0.1888, 0b24845f≈0.80, 0c582fdc≈0.00);
   fresh-frame cap (20 <= 30 step cap, <= 60 global cap).
5. Score with `python3 scripts/score.py --dry-run` — N/A (analysis-only, no
   graphs produced; no scorer input).

## Budget

12h T4 budget — estimated <5 min CPU (60 DoG ~30 s at 0.4 s/frame +
20 fresh detects ~40 s + moments/percentiles). No GPU, no uploads.
Fresh detection frames: 20 (cap 30 for this step, 60 global).
