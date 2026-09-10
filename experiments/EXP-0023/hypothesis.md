# EXP-0023 — Full-video DS both samples

## Hypothesis

Half-resolution (downsample=2) DoG detection preserves full-video tracking
quality on both embryo samples while cutting detection time ~4x, qualifying
as a GO kernel upgrade for the detection stage (H-005 timing path).

## Background

- docs/PROTOCOL.md v1.1 (frozen metric: adjusted edge Jaccard + 0.1 * division Jaccard).
- EXP-0008: full-video full-res @99.0 reference (44b6 operating point).
- EXP-0009: full-video full-res @98.5 reference (6bba operating point).
- EXP-0022: window (t20-29+t40-49, 6bba) DS parity — recall/raw/ec IDENTICAL
  to full-res, adj up, det -21%, 3.75x speedup. This experiment tests whether
  the window result generalizes to full video on both samples.

## Falsification criteria

GO kernel upgrade iff ALL hold per sample vs recomputed full-res refs:
recall_micro within 0.01 AND edge_raw within 0.005 AND edge_adj >= ref.
Else STOP (no kernel upgrade).
