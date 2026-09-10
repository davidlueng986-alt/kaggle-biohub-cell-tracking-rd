# EXP-0025 — Linking-time profile

## Hypothesis
After the EXP-0022 detection collapse (0.22 s/frame half-res), Hungarian
linking (`scripts/baseline_link.py`: scipy C path for N>60, pure-python
below, 7 µm gate) is now the dominant cost on dense videos, and per-pair
link seconds scale ~N^3 (O(n^3) assignment per adjacent frame pair).

## Background
- `docs/PROTOCOL.md` (scorer gate 7 µm; causal linking assumptions).
- H-005 timing envelope: 80–96 s/video on the Kaggle submit path.
- EXP-0022: detection 3.8x collapse via half-res (0.22 s/f).
- Linker under test: `scripts/baseline_link.py` (`BL.link`, `BL._assign`,
  `BL._pair`); frozen det artifacts `experiments/EXP-0009/full_*.json`,
  `experiments/EXP-0012/full_t*.json`.

## Falsification criteria
- Dominance: linking is "dominant" iff link_s > detect_s (share > 50% of
  detect+link) on the dense video; "material" iff share > 10%.
- Scaling: pooled log-log fit of per-pair seconds vs N over all 297 pairs
  (N range ~40–212) must yield exponent b in [2.5, 3.5] to sustain ~N^3.
  b < 2.0 rejects the cubic-scaling claim.
