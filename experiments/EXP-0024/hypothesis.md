# EXP-0024 — Per-sample threshold map

## Hypothesis
At least one fixed DoG percentile threshold in {97.5, 98.0, 98.5, 99.0, 99.5}
rescues detection recall to >= 0.90 on EACH of the three EXP-0021 failing
samples (44b6_0b24845f, 44b6_0c582fdc, 6bba_05db0fb1) over window t=20..29 —
i.e. the transfer failure is a per-sample level mis-set, not a detector
blindness, and a fixed pct exists per sample worth promoting to full video.

## Background
- docs/PROTOCOL.md (v1.1 frozen metric; this rung is recall-only, see scope).
- EXP-0021: per-embryo levels transfer on refs (0113de3b rec 1.000 @44b6/99.0,
  05b6850b rec 0.893 @6bba/98.5) but fail on 0b24845f (0.325), 0c582fdc
  (0.197), 05db0fb1 (0.290). Diagnosis: annotated cells dimmer than the
  percentile cutoff; fixed percentiles may not transfer.
- Detector: scripts/dog_detect.py, frozen sigmas (1,3,3)/(1.6,5,5), min-size
  50. Matcher: scripts/score.py match_nodes (7um per-timepoint optimal).

## Falsification criteria
TRANSFER-RESCUED iff all three samples reach window recall >= 0.90 at some
swept pct; otherwise NOT-RESCUED. Best pct per sample = highest recall, ties
broken by lower det/frame. A NOT-RESCUED verdict rejects "fixed-pct rescue"
and routes to intensity-aware (MAD/thr-mode, EXP-0022-style) or scale-variant
detection — no full-video follow-up at any swept level is justified on recall
grounds alone.
