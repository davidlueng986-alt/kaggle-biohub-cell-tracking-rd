# Notes — EXP-0025 Linking-time profile

## Log
- Created via `scripts/new_experiment.sh`.
- Ran `profile_link.py`: 3 videos x 99 pairs = 297 timed `_pair` calls,
  total wall ~3 s (far under the 20-min budget; no leg aborted).

## Decisions
- Timed `BL._pair` (not `BL._assign` alone) so the per-pair number includes
  the pure-Python O(N^2) cost-matrix build — this turned out to be the
  right call: on the dense median pair, build is ~88% of pair time
  (9.73 ms build vs 1.33 ms scipy solve), i.e. the "O(n^3) Hungarian"
  worry misidentifies the actual hotspot.
- Warmed up the scipy import outside timed regions (first call cost
  ~0.33 s: 0.3357 s cold vs ~0.0086 s warm on the same dense pair).
- Global re-id `t*100000+local_id`; driver edge sums match full `BL.link`
  runs exactly on all 3 videos; median-pair re-run is bit-identical
  (deterministic).
- Actual artifact params differ slightly from the mission brief
  (44b6 files carry `pct: 98.5`, not 99.0; dense N range 166–212, median
  191) — reported actuals, not brief values.
- EXP-0012 det nodes carry NO per-node `split` flag (only `n_split` in
  params), so `BL.link` takes the single-phase path (`phased: False`) on
  all 3 videos — the two-phase path was not exercised.
- Headline scaling uses the pooled fit (N 40–212, R^2=0.79); per-video
  fits are reported but unstable (narrow N range, R^2 0.14–0.55).

## Results (see metrics.json + pair_times_*.csv)
- dense_44b6: link 1.12 s vs detect 231.68 s → 0.5% (negligible).
  99/99 pairs scipy path, median 11.6 ms/pair.
- sparse_6bba: link 0.20 s vs detect 84.99 s → 0.2% (negligible).
  99/99 pairs pure-python path (N 40–58, all <= 60), median 1.5 ms/pair.
- split_6bba: link 0.15 s vs detect 93.47 s → 0.2% (negligible).
  83 scipy / 16 pure, median 1.3 ms/pair.
- Pooled scaling exponent b=1.51 (matrix-build-dominated, NOT ~N^3).
- Hypothesis FALSIFIED on both counts: linking is not dominant anywhere,
  and scaling is ~N^1.5, not ~N^3.
- Context: even under EXP-0022 half-res detection (~22 s/video), dense
  link share would be only ~1.12/23 ≈ 5% — still not dominant. Linking is
  ~1% of the H-005 80–96 s/video envelope. Detection remains the target.

## Decisions (paydown — RECOMMEND ONLY, implemented nothing)
- If linking ever matters (much denser videos): gate-prefiltered candidate
  lists + connected-component split per pair (many tiny Hungarians instead
  of one dense NxN), and spatial hashing (~7 µm grid) for ~O(N) candidate
  lookup. Both preserve the exact gated optimum — pure overhead removal.
- Pair chunking not recommended as primary (pairs are already atomic).
