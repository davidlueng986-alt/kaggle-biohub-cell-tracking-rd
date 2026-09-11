# Notes — EXP-0058 Threshold-hysteresis union probe on 05db0fb1

## Log

- 2026-09-11: chose Option A over B — threshold-hysteresis tests the
  documented merge-displacement mechanism (EXP-0011/0057 STOP-DESCENT)
  on the current frontier operating point with a crisp directional
  prediction plus an informative null (union==@95 proves monotonicity);
  Option B's mechanism (small-σ recovers "dim" cells) conflates size
  with intensity and was already weakened by EXP-0014 (small-σ alone
  lost recall even on bright tissue).
- 2026-09-11: `bash experiments/EXP-0058/run.sh` → exit 0, STOP.
  20 CLI detections, ~14 s detection wall (0.68–0.69 s/f both
  thresholds — vectorized path; dense tissue no longer a cost driver).

## Results (6bba_05db0fb1, t20–29, 143 GT nodes)

- @99.0 alone: recall 0.1189 (17/143), 221.6 det/f.
- @95.0 alone: recall 0.6923 (99/143), 476.8 det/f
  (window harder than full-video 0.750 — expected, GT-dense slice).
- Union (@99 anchors + @95 halo ≥3 µm from anchors): recall 0.6993
  (100/143), 559.7 det/f; halo kept/dropped 3381/1387.
- Marginal: +1 GT node (id 21000300) for +829 detections → cost 829
  per match vs GO bar ≤ 10. STOP by pre-registered criterion.

## Decisions

- `keep-trying` (ceiling; window rung, not a promotion claim).
- STOP threshold-hysteresis direction: the merge-displacement
  non-monotonicity EXISTS (exactly one @99 anchor matched a GT node its
  @95 counterpart lost — mechanism micro-confirmed) but is practically
  negligible: anchors are ~63% redundant with halo (1387/4768 dropped),
  and the surviving +829 anchors buy a single node. The halo at @95 is
  overwhelmingly clutter, not displaced cells — consistent with
  EXP-0057's verdict that merging/displacement dominates below @95.
- Single-threshold policy stands (@95.0 on 05db0fb1). No full-video
  follow-up. Do not repeat threshold-fusion; next recalls must come
  from a non-threshold mechanism (learned detector, EXP-0035 track).
