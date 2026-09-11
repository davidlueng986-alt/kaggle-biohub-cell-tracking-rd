# Notes — EXP-0045

## Result
Verdict GO: 3 LOST-AT-DETECTION + 1 LOST-AT-LINKING, 0 RECOVERED.

## Per-division detail
- 6bba_05db0fb1:25000381 (t24->t25): parent 12.19 um (unmatched), d1 12.28 um
  (unmatched), d2 -> pred 7285 @1.68 um. Nearest detection to d1 IS 7285 too:
  sisters merged into one detection. LOST-AT-DETECTION.
- 6bba_05db0fb1:53001011 (t52->t53): parent -> pred 14683 @6.81 um (borderline
  match, edges 14442->14683->14932 single chain); d1 7.38 um, d2 9.38 um, both
  unmatched. LOST-AT-DETECTION.
- 6bba_05db0fb1:63001217 (t62->t63): all unmatched, nearest 12.9-13.4 um.
  LOST-AT-DETECTION.
- 6bba_062c8d37:90001276 (t89->t90): all matched <= 1.73 um
  (4549/4593/4598). GT daughter distance 9.08 um, detected 9.49 um (geometry
  preserved). Linker output: 4502->4549->4593 single chain; 4598 orphan
  (no incoming, out 4598->4646). Zero fork nodes (out-degree >= 2) in BOTH
  pred samples. LOST-AT-LINKING.

## Mechanism
The IMAGE-graph linker is structurally 1-to-1 (Hungarian-style assignment):
with zero forks emitted anywhere, a present daughter (4598, 1.72 um from GT)
is left parentless because the parent slot is already consumed by 4593.
EXP-0044's r10 fork rule fired 35 FPs / 0 TPs because a radius-only fork
criterion cannot pick the true orphan out of dense clutter; it adds edges
where no division exists while missing the one site with evidence.

## EXP-0046 direction (recommended, NOT implemented)
Orphan-driven second-edge pass: after the 1-to-1 link, for each detection
with no incoming edge whose nearest GT-agnostic neighbour frame pair fits a
division site (a linked parent->child chain within ~10 um + the orphan within
gate of the parent), add parent->orphan as a fork edge. Gate strictly on
orphan-ness + proximity so it cannot fire on already-linked clutter (the
EXP-0044 FP source). Validate on these 4 sites first (expect: +1 TP at
90001276, +0 FP at the three detection-lost sites), then frozen CV.

## Caveats
- Filenames verified: EXP-0021 uses `<sid>_pred.json` as stated; GT lives in
  EXP-0003/gt/ (not EXP-0003/ root).
- match_nodes threshold inclusive at 7.0 um; div2 d1 at 7.38 um is just
  outside gate — borderline, still correctly LOST-AT-DETECTION.
