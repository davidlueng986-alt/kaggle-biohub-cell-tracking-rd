# Notes — EXP-0060 Sign-corrected nested binary-brightness rule (HIGH-B→96)

## Log

- Scaffolded via scripts/new_experiment.sh (EXP-0060 was free).
- hypothesis.md + plan.md written BEFORE any new numbers (levels 96.0/99.0
  frozen, sign-corrected median-split rule, gate 7).
- Brightness B(S) recomputed fresh (t20–29, 60 frame reads): IDENTICAL to
  EXP-0059/brightness.json (all 6 within 1e-6; assert in brightness.py).
  Assignments flipped per pre-reg: LOSO 0113de3b@99, 0b24845f@96,
  0c582fdc@96, 05b6850b@99, 05db0fb1@96, 062c8d37@99.
- Scope note (pre-reg brief said only 062c8d37@99 was missing): the
  corrected nested arm fit-6bba→44b6 assigns ALL three 44b6 samples @96
  (every 44b6 B exceeds the 6bba fit-median 85.89), and 0113de3b@96 was
  never detected. Fresh exactly 200f (at the ≤200 cap): 062c8d37@99 +
  0113de3b@96, dog_detect.main in-process, exact CLI path/defaults.
- link (BL.link gate 7, gid reassignment) + score (score_samples v1.1.0;
  EXP-local scipy swap, equivalence gate PASS: 0113de3b@99 ec 47/2/3
  identical both backends; scripts/* untouched).
- Frozen rescore sanity: 0113de3b@99 edge 0.9382 reproduces EXP-0008/0021;
  05db0fb1@96 edge 0.4822 reproduces EXP-0039; 05b6850b@99 edge 0.7121
  reproduces EXP-0008 (gate-7 row).

## Results (PROTOCOL v1.2, scorer v1.1.0, cv_tag trusted, complete 6/6 + 3/3)

- LOSO (sign-corrected): 0113de3b@99 1.0382; 0b24845f@96 0.2872;
  0c582fdc@96 0.2874; 05b6850b@99 0.8121; 05db0fb1@96 0.4822;
  062c8d37@99 0.7988. loso_worst = 0.2872 (> BTE 0.2092 ✓);
  micro_edge = 0.6272 (> BTE 0.4826 ✓); div_micro = 0.0.
- Nested: fit-44b6→6bba micro 0.6406; fit-6bba→44b6 micro 0.3631;
  nested_worst = 0.3631 (< BTE 0.4193 ✗).
- Bars: 2/3 → CANDIDATE bar FAILED. Not a promotion claim (ceiling rung).
- New reads: 062c8d37@99 edge 0.7988 ≈ @96 0.7860 (bright-tissue @99
  confirmed, no rescue needed); 0113de3b@96 edge 0.7804 vs @99 0.9382
  (pure count cost on bright reference: ec 43/6/7 vs 47/2/3).

## Decisions

- `keep-trying` — sign correction RESCUES LOSO (worst 0.161→0.287,
  micro 0.433→0.627, both above BTE) but the nested arm fit-6bba→44b6
  falsifies the binary rule as a BTE challenger (0.3631 < 0.4193).
- Mechanism: the 3-sample embryo fit-median is brittle — median of
  [62, 86, 1002] is 86, so the ENTIRE 44b6 embryo (B 256–1009) lands on
  one side (@96), forcing the bright reference 0113 onto a count-costly
  level while dark 44b6 samples at @96 (edge ~0.187) gain too little to
  beat BTE's uniform-97 arm. A 1-bit global cut cannot express
  "44b6-dark needs 96 but 44b6-bright needs 99" — the regime boundary is
  not embryo-portable at this sample size.
- Next-stage input: binary brightness rules EXHAUSTED (both signs tested
  under nested HPs; best nested_worst 0.3631). Do not re-run sign
  variants. Candidate directions: continuous/per-sample estimators
  (learned, EXP-0035 path) or accept per-sample selection cost honestly.
- Scope compliance: created under experiments/EXP-0060/ only; no
  scripts/docs/knowledge/other-experiment/data edits; no pip; no kaggle;
  no commits; 200/200 fresh-frame budget; no secrets; no zarr copied.
