# Notes — EXP-0046

## Result
Verdict STOP. Orphan-driven second-edge pass parked alongside r10.

## Numbers (score.py v1.1.0, true T_true, base recomputed in-run)
- 6bba_062c8d37 base: edge TP/FP/FN 781/20/117, recall 0.8697, raw 0.8508,
  adj 0.8647; div TP/FP/FN 0/0/1.
- 6bba_062c8d37 pass: edge TP/FP/FN 784/32/114, recall 0.8731, raw 0.8430,
  adj 0.8568 (REGRESSION -0.0079); div TP/FP/FN 1/18/0.
- 6bba_05db0fb1 base: edge TP/FP/FN 251/92/932, recall 0.2122, raw 0.1969,
  adj 0.2092; div TP/FP/FN 0/0/3.
- 6bba_05db0fb1 pass: edge TP/FP/FN 258/168/925, recall 0.2181, raw 0.1910,
  adj 0.2029 (REGRESSION -0.0063); div TP/FP/FN 0/2638/3.
- Added edges: 69 (062c8d37) / 3904 (05db0fb1); new forks: 69 / 3904.
  Base reproduces frozen EXP-0021 edges bit-exactly (4440/4440, 21665/21665);
  pass re-run is bit-identical (deterministic).

## Per-bar outcome
- Main: div TP 0->1 (the audited 90001276 site IS recovered: fork
  4549->[4593, 4598] matches GT parent + both daughters) BUT div FP 0->18
  and edge adj 0.8647->0.8568. Bar needs FP==0 AND adj >= base -> FAIL.
- Control: 3904 new forks vs required zero -> FAIL.

## Mechanism
Orphan-ness is not selective. In dense detected fields, no-incoming nodes
are common (births, detection gaps, track ends) and almost always sit within
10um of some linked target, so the incoming-less gate fires on clutter just
as the r10 radius gate did (EXP-0044: 35 div-FPs; here: 18 + 2638 div-FPs).
The true orphan (4598) is recovered, but indistinguishably buried: +3 edge
TP for +12 edge FP on 062c8d37, +7 TP for +76 FP on 05db0fb1. A proximity +
orphan-ness criterion cannot pick the division daughter out of dense clutter
without a stronger division-specific signal (e.g. daughter-daughter
co-location/geometry or appearance change at the site).

## Caveats
- Gid re-id is near-identity here (EXP-0021 ids already globally unique and
  (t,id)-ordered), so audit ids (4549/4593/4598) carry over; scorer matches
  on geometry regardless.
- Division FP counts use the scorer's evaluable-fork rule (conservative);
  raw added-fork counts (69/3904) are the no-harm signal and both fail it.

## Next
No EXP-0047. Orphan rule parked with r10. Future division work needs a
signal beyond proximity+orphan-ness; the 4-site audit (EXP-0045) stands as
the frozen evidence base.
