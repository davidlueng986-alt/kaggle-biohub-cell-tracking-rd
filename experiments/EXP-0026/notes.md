# Notes — EXP-0026 ROI-masked DoG acceleration (H-005)

## Log

- Scaffolded via `scripts/new_experiment.sh` (repo root).
- Wrote `roi_detect.py`: experiment-local wrapper IMPORTING frozen
  `dog_detect.detect` (scripts/* untouched). Mask = strided half-res
  intensity (`vol[:, ::2, ::2]`, no interpolation) → adaptive percentile q
  → half-res labeling → per-component boxes via `find_objects` → full-res
  coords (×2) + halo (6,16,16) → per-box `detect(crop, pct=98.5)` →
  offset + exact-dedupe. Deterministic (sorted boxes/nodes).
- Prototypes on t20 (not the gate, informed the design): union bbox of even
  a q=98 mask covers 99.2% of voxels (cells fill the frame) → single-crop
  ROI is dead; multi-box q=98 sum-expanded-box = 51% of voxels (halo
  overhead already bites: q=90 sums to 171% of full). Per-box @98.5 gave
  n=96 vs FULL 43 with rec 6/8; pct=99.0 worsened recall (4/8); halo-24
  worsened FPs (n=122); MAD k=12 recovered all FULL dets but n=171.
  Diagnosis: all 43 FULL dets lie inside boxes and all 8 GT in-mask — misses
  AND extras are pure threshold effects (per-box percentile too high in
  bright boxes, too low in dim ones). No single per-box pct fixes both.
- `bash experiments/EXP-0026/run.sh` → exit 0, gate STOP recorded (×2 runs,
  bit-consistent verdict; numbers below from final run).

## Results (window t20–29+t40–49, GT subgraph 167 nodes / 148 edges, T~1272)

- FULL @98.5 (fresh recompute): rec 0.9820 (164/167), det 911,
  raw 0.9533 / adj 0.9804, ec 143/2/5, 1.260 s/f.
- ROI q=98 (primary): rec 0.7725 (129/167, d −0.2096), det 1987 (2.2×),
  raw 0.4105 (d −0.5428) / adj 0.3875, ec 78/42/70, 0.640 s/f.
- ROI q=95 (Pareto): rec 0.8862, det 2532, raw 0.3913 / adj 0.3525,
  ec 81/59/67, 0.964 s/f.
- Speedups (wall, incl. ~0.4 s/f interpreter+zarr startup): q98 1.97×,
  q95 1.31×. Inner (detect-only, excl. startup): q98 ≈ 0.17 vs 0.85 s/f.
- Gate needed dRecall ≥ −0.01 AND dRaw ≥ −0.005 AND ≥ 2× → FAIL on all
  three for q98 (q95 fails speed AND both quality bars). Pareto is strict:
  the speed-passing config craters quality; the quality-closer config is
  slower AND still far off parity. Same shape as EXP-0023 (speedup real,
  parity the blocker).

## Bottleneck breakdown (t20 micro-profile, in metrics.json timing_breakdown)

- FULL 0.81 s: gaussian pair 0.288 s (36%) + percentile/label/bincount
  0.067 s (8%) + per-component `argwhere(lab==i)` scans 0.452 s (**56%**,
  48 components × full-mask scans; detector-internal, unreachable from a
  wrapper since scripts/* are frozen).
- ROI q98 0.17 s inner: mask 0.010 s (**6%**, find_objects keeps it cheap)
  + per-box loop 0.164 s (inner detect sum 0.10 s; rest = 45 crops +
  per-call overhead — box COUNT, not voxel count, is the floor).
- Wall speedup diluent: per-frame process startup + zarr open ≈ 0.4 s/f
  applies equally to both arms (FULL 1.26 vs ROI 0.64 s/f wall).

## Decisions

- STOP — ROI masking as formulated does not pay: per-box adaptive
  thresholds cannot reproduce the global operating point (structural, both
  directions at once), and foreground fills the frame (union ROI ≈ full).
- EXP-0028 (full-video) NOT run; stays a recommendation only, and only
  behind a redesign: (a) global-threshold transfer into per-box detection
  (needs `detect()` to accept an absolute thr — a scripts/* change, out of
  scope here); or (b) single-pass masked DoG (skip gaussian outside mask —
  needs detector-internal change); or (c) attack the 56% argwhere cost
  (one vectorized pass, e.g. single argsort/find_objects partition inside the
  detector). All are detector edits → parked for a future experiment with
  scripts/* scope.
- FP-explosion → edge-collapse repeats the EXP-0013 lesson (fewer, better
  detections win; +118% dets → raw −0.54 here).
