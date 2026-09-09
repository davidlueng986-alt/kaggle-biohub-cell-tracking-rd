# RESULTS ledger

Newest rows append at the bottom. `decision` ∈ {promote, keep-trying, reject}.
Schema: `exp_id | hypothesis | config / seed | embryo-CV (edge / div / score) | LB (diag) | decision | notes`.
Every row must link hypothesis → result → decision (no bare scores).

| exp_id  | hypothesis | config / seed            | embryo-CV (edge / div / score) | LB (diag) | decision     | notes                  |
|---------|------------|--------------------------|--------------------------------|-----------|--------------|------------------------|
| EXP-0000 | H-001     | template, no run         | —                              | —         | keep-trying  | Example row; folder template only, not a real result. |
| EXP-0001 | H-001 | toy dry-run, simplified scorer, hand-checked | fold0-toy 0.500 / 1.000 / 0.600; fold1-toy 0.333 / 0.000 / 0.333 | — | keep-trying | Harness-only (no real data); fold0 matches hand calc; H-001 transfer claim untested → needs data + full geff scorer (EXP-0002). |
