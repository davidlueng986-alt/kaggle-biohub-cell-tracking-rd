# Plan — EXP-0054 GT-free count target analysis (T_ratio vs edge)

## Config / seeds

Deterministic stdlib-only analysis (python3, no seed needed); frozen inputs =
10 metrics.json files listed in `run.sh`; no detection/linking, no score
recomputation, CPU seconds.

## Steps

1. `bash experiments/EXP-0054/run.sh` — harvests 13 unique
   (T_ratio, det/frame, edge_raw, edge_adj) rows with source EXP per row,
   cross-checks values against frozen sources (asserts, fails loudly on drift),
   computes T_ratio bins ([0–0.5, 0.5–0.8, 0.8–1.0, 1.0+]), hand-rolled
   Spearman(T_ratio, raw) and Spearman(det/f, raw), per-sample best points +
   low-T→high-T deltas, writes `metrics.json` with verdict.
2. Exclusions (ledgered in metrics.json): EXP-0008 rows (n_det_total copies
   window-probe means, T underivable), EXP-0010 combo (dup of EXP-0009 ops),
   rescore bars (bit-identical dups), EXP-0044 fork arm (linker-only variant).
3. Read `metrics.json` verdict + spans; copy numbers to RESULTS/STATE input.

## Budget

< 20 min, CPU-only arithmetic on small JSONs (actual: seconds).
