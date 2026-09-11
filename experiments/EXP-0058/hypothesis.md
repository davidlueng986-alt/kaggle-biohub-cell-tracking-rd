# EXP-0058 — Threshold-hysteresis union probe on 05db0fb1

## Hypothesis

Two-threshold hysteresis union beats the single operating point on
detection recall at controlled count cost: on dense/dim sample
6bba_05db0fb1 (current operating point @95.0, STOP-DESCENT declared at
@94.5 in EXP-0057), the union of @99.0 (bright-core anchors) + @95.0
detections farther than 3 µm from any anchor (dim halo fill) recovers
GT cells that the @95.0 threshold merges/displaces past the 7 µm match
radius, at a marginal cost of ≤ 10 extra detections per extra matched
GT node.

## Background

- EXP-0011: lowering the threshold merges dense cells (centroids
  displace past 7 µm) — descent overshoots. EXP-0055→0057: descent
  96.0→95.5→95.0→94.5 kept paying until @94.5 (TP +1 vs FP +18) —
  merging/displacement dominates. @95.0 (recall 0.750 full-video) is the
  standing operating point.
- EXP-0014 D/E (scale-fusion) failed on edge readout — but that was
  scale-gating (small-σ fragments), a different mechanism from
  threshold-gating. This probe is detection/recall-only (no linking), so
  it isolates the detection-level mechanism cleanly.
- Key subtlety making this falsifiable rather than vacuous: if the
  threshold response were monotone (@99.0 detections ⊆ @95.0
  detections), the union would equal @95.0-alone exactly and the
  mechanism is falsified — proving single-threshold sufficiency. A union
  win is only possible via non-monotonicity (merge-displacement), the
  documented EXP-0011 mechanism.

## Falsification criteria

Single-sample operating-point probe (window t20–29, HPs fixed a priori,
no selection; ceiling keep-trying, NOT a promotion claim).

- GO iff recall(union) > recall(@95.0-alone) strictly (≥ 1 extra GT
  node) AND marginal cost (extra_det / extra_matched) ≤ 10 →
  recommend full-video follow-up (do not run here).
- STOP otherwise (union == @95.0 → monotone/subset, mechanism dead; or
  win too expensive → halo is clutter, not cells).
