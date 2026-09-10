# EXP-0013 — Prominence-gated splits + conservative linking (H-002)

## Hypothesis

EXP-0012's FP explosion (30→168) comes from two separable causes:
weak-peak over-splits (elongated singles clearing the footprint twice)
and fragments stealing/linking near GT tracks. Both are gateable without
GT: (a) prominence — secondary peaks must reach ≥0.7× the primary DoG
value or no split (kills weak over-splits); (b) conservative two-phase
linking — primaries claim links first against all targets, split parts
link only to leftovers (fragments cannot steal base links). Predicts on
the density-spanning window (t20–29 + t40–49, includes miss frames
42,43,44): config D (@98.0+split+prom0.7+phased) matches-or-beats the
@98.5 base (A) on recall AND window edge (raw + adj) with fewer splits
than ungated B; B alone repeats EXP-0012's pattern (recall up, edge down).
Gate: D ≥ A on all three readouts → full-video GO (EXP-0014); else stop.
Ceiling keep-trying (window rung; promotion needs full-video + replication).

## Falsification criteria

- REJECT gated splitting if D falls below A on any of recall / raw / adj
  (then prominence+phasing do not pay → splitter family parked; pivot to
  dim-cell scale terms or H-003 appearance).
