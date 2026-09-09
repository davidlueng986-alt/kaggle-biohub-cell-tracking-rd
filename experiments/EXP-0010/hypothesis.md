# EXP-0010 — Per-embryo combo + @98.0 window probe (H-002)

## Hypothesis

Per-embryo operating levels beat any uniform percentile: the combo
(44b6@99.0 from EXP-0008 + 6bba@98.5 from EXP-0009) matches-or-beats both
uniform policies on every reported aggregate (per-sample adj, embryo
micros, worst-fold), because each arm was selected on its own sample's
tradeoff (44b6: extra counts cost with zero gain; 6bba: recall buys more
than counts cost). Separately, 6bba@98.0 on the t0–9 window reaches recall
1.00 — justifying a full-video @98.0 run (EXP-0011) for the dim tail;
if it does not, the descent stops here (level family exhausted → size/
appearance terms needed). Combo assembly reuses frozen artifacts (no new
detection); only the 10-frame @98.0 probe is new compute. Ceiling
keep-trying (assembly + probe, single deterministic pass; promotion needs
fold0 win + replication).

## Falsification criteria

- REJECT combo-superiority if any aggregate (per-sample adj, either micro,
  worst-fold) falls below the corresponding uniform-policy value.
- REJECT @98.0 descent if window recall < 1.00 (then stop descending).
