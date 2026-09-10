# Plan — EXP-0025 Linking-time profile

## Config / seeds
- Deterministic, CPU-only, read-only analysis. No seeds (linker is
  deterministic; verified by re-running the median pair per video).
- Frozen inputs (verify with `ls` — counts as run):
  - `experiments/EXP-0009/full_44b6_0113de3b_t*.json` (100 frames, dense)
  - `experiments/EXP-0009/full_6bba_05b6850b_t*.json` (100 frames, sparse)
  - `experiments/EXP-0012/full_t*.json` (100 frames, 6bba @98.0+split params)
- `scripts/baseline_link.py` is imported read-only; never modified.

## Steps
1. Global re-id per video (`id = t*100000 + local_id`; per-frame ids
   restart at 1 and would collide in `BL.link`).
2. Warm up scipy import (`BL._assign` on a 61x61 dummy) OUTSIDE timed
   regions so the one-time import (~0.33 s) does not pollute pair timings.
3. Run `./experiments/EXP-0025/run.sh` — times each of the 99 adjacent
   pairs per video with `time.perf_counter` around `BL._pair`, records
   N/backend/edges, decomposes one median pair per video into
   cost-matrix-build vs `_assign`-solve, cross-checks driver edge sum vs a
   full `BL.link` run, and writes `metrics.json` + `pair_times_*.csv`.
4. Per-video 12-minute abort guard (breaks the pair loop, marks leg
   partial). Total runtime ~seconds; budget < 20 min.
5. Verdict rule: share > 50% dominant / > 10% material / else negligible;
   pooled log-log exponent over all 297 pairs is the headline scaling
   number (per-video N ranges are too narrow for stable fits).

## Budget
CPU minutes only; measured wall ~3 s for the full 3-video profile.
