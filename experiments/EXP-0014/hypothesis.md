# EXP-0014 — Dim-cell small-σ fused detection (H-002)

## Hypothesis

Dim missed cells are smaller/dimmer than the base DoG scale ((1,3,3)/
(1.6,5,5)) is tuned for: a small-σ pass ((0.7,2,2)/(1.1,3.2,3.2)) responds
to them, and NMS fusion (novel small-σ detections only — within 3 µm of a
base detection the base wins) adds recall without duplicating cells.
Predicts on the gate window (t20–29 + t40–49): config A reproduces
EXP-0013 A EXACTLY (rec 0.982, raw 0.9533 — determinism check, asserted);
fused D/E match-or-beat A on recall AND raw AND adj with modest count
growth. Gate: a fused config ≥ A on all three → full-video GO (EXP-0015);
small-σ alone (B/C) is expected to underperform base alone (small scale =
more fragments) — included to isolate fusion value. Ceiling keep-trying
(window rung).

## Falsification criteria

- REJECT scale-fusion if no fused config beats A on all three readouts
  (then dim cells need more than scale — appearance or learned detector).
- REJECT pipeline determinism if A ≠ EXP-0013 A exactly (bug hunt, no science).
