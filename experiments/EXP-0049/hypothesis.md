# EXP-0049 — Drift re-audit submit_gold after GATE_UM 7.0 + find_wheels edits

## Hypothesis
The current `notebooks/submit_gold/submit_gold.ipynb` is behaviorally IN-SYNC with
the repo sources of truth (`scripts/dog_detect.py::detect`,
`scripts/baseline_link.py::link`/`_assign`, `scripts/graphs_to_csv.py` writer rules)
after the two post-EXP-0036 edits (GATE_UM 10.0→7.0, hardcoded wheels path →
search-based `find_wheels`); i.e. all static checks and equivalence probes pass.

## Background
- Prior audit EXP-0036 passed on an OLD notebook version; two edits landed since.
- Expected config: GATE_UM = 7.0 exactly once / no 10.0; search-based find_wheels;
  per-embryo pct map 44b6→99.0 / 6bba→98.5 / default 98.5; no forks.

## Falsification criteria
ANY behavioral probe inequality (detect positions, linked edges, assign permutation)
→ verdict DRIFTED, hypothesis rejected. Static-check failure alone is reported but
only a behavioral inequality flips the verdict per mission spec (statics all pass here).
