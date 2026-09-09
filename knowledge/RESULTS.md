# RESULTS ledger

Newest rows append at the bottom. `decision` ∈ {promote, keep-trying, reject}.
Schema: `exp_id | hypothesis | config / seed | embryo-CV (edge / div / score) | LB (diag) | decision | notes`.
Every row must link hypothesis → result → decision (no bare scores).

| exp_id  | hypothesis | config / seed            | embryo-CV (edge / div / score) | LB (diag) | decision     | notes                  |
|---------|------------|--------------------------|--------------------------------|-----------|--------------|------------------------|
| EXP-0000 | H-001     | template, no run         | —                              | —         | keep-trying  | Example row; folder template only, not a real result. |
| EXP-0001 | H-001 | toy dry-run, legacy path of v1.1 scorer, hand-checked | fold0-toy 0.500 / 1.000 / 0.600; fold1-toy 0.333 / 0.000 / 0.333 | — | keep-trying | Harness-only (no real data); fold0 matches hand calc; re-scored under PROTOCOL v1.1 (same numbers, new envelope). H-001 transfer claim untested → needs data + geometric scorer (EXP-0002). |
| EXP-0002 | H-001+H-004 | geometric toy, v1.1 faithful scorer, deterministic (no seed) | fold0-perfect 1.000/1.000/1.100; fold0-idswitch 0.333 div — /0.333 (FP≥1); fold0-inflated adj 0.900 (penalty 0.9×); fold1-perfect 1.000/1.000/1.100; fold1-nodiv div FN≥1 | — | keep-trying | Geometric path validated (perfect/idswitch/inflation/division behave per spec, 6/6 checks); no real data → NOT promotable. Next: EXP-0003 real embryo-CV baseline after Rules acceptance + download. |
