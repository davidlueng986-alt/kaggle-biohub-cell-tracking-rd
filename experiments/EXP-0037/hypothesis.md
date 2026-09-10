# EXP-0037 — Submit-output rescore (submit truth)

## Hypothesis

The v6 kernel output (visible 4-sample CSV) parses to graphs that score
under v1.1 as: 0113de3b raw 0.636/adj 0.661, 0b24845f 0.096/0.102, 05b6850b
0.793/0.813, 05db0fb1 0.181/0.192 — i.e. detection reproduces local refs
byte-identically (parser verified against score.py's own CSV loader) and
ALL deviation vs gate-7 local refs is link-stage gate-10-vs-7 churn
(FPs 2→16, 2→3, 30→39, 92→150). Gate choice is a tunable with highly
non-uniform per-embryo effect (0113de3b −0.28 adj vs 05b6850b −0.006),
not a no-op. The submit config is validated end-to-end (parses clean,
formats legal, detection exact) at these numbers. Ceiling keep-trying
(measurement rung; no promotion content — nothing beats any bar here).

## Falsification criteria

- REJECT the parse (re-derive) on any row-count/node-id/coordinate mismatch
  vs the CSV (then the numbers below are ungrounded).
