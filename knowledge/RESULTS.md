# RESULTS ledger

Newest rows append at the bottom. `decision` ∈ {promote, keep-trying, reject}.
Schema: `exp_id | hypothesis | config / seed | embryo-CV (edge / div / score) | LB (diag) | decision | notes`.
Every row must link hypothesis → result → decision (no bare scores).

| exp_id  | hypothesis | config / seed            | embryo-CV (edge / div / score) | LB (diag) | decision     | notes                  |
|---------|------------|--------------------------|--------------------------------|-----------|--------------|------------------------|
| EXP-0000 | H-001     | template, no run         | —                              | —         | keep-trying  | Example row; folder template only, not a real result. |
| EXP-0001 | H-001 | toy dry-run, legacy path of v1.1 scorer, hand-checked | fold0-toy 0.500 / 1.000 / 0.600; fold1-toy 0.333 / 0.000 / 0.333 | — | keep-trying | Harness-only (no real data); fold0 matches hand calc; re-scored under PROTOCOL v1.1 (same numbers, new envelope). H-001 transfer claim untested → needs data + geometric scorer (EXP-0002). |
| EXP-0002 | H-001+H-004 | geometric toy, v1.1 faithful scorer, deterministic (no seed) | fold0-perfect 1.000/1.000/1.100; fold0-idswitch 0.333 div — /0.333 (FP≥1); fold0-inflated adj 0.900 (penalty 0.9×); fold1-perfect 1.000/1.000/1.100; fold1-nodiv div FN≥1 | — | keep-trying | Geometric path validated (perfect/idswitch/inflation/division behave per spec, 6/6 checks); no real data → NOT promotable. Next: EXP-0003 real embryo-CV baseline after Rules acceptance + download. |
| EXP-0003 | H-001+H-002 | real subset 6, oracle GT nodes + causal Hungarian linker, deterministic | 44b6-micro 1.0933 / 6bba-micro 1.0705 / worst 1.0705 (edge); div sums 0/0/4 (no forks; 44b6+05b6850b div 1.0-empty, 05db0fb1+062c8d37 div 0.0) | — | keep-trying | First REAL-DATA result (floor, not a model): 55 GT edges missed, 4 div FNs. Baseline for H-002 ladder; promote only on fold0 win + no fold1 regression ≥2 seeds. Next: EXP-0004 fork-proposing variant (done). |
| EXP-0004 | H-002+H-003 | real subset 6, oracle links + radius-15µm fork proposals (≤1/source), deterministic | fold0 44b6 1.0933→1.0933 (+0.0000); fold1 6bba 1.0705→1.0680 (−0.0025); div sums 0/0/4→3/10/1 (05db0fb1 0→0.18, 062c8d37 0→0.5, 05b6850b 1.0→0.0 spurious) | — | keep-trying | Sub-gate REJECT for promotion (div gain real but edge regresses fold1; single-seed cap anyway). Signal: 3/4 GT divisions recoverable geometrically. Next: EXP-0005 tighter gating (smaller radius / component veto / appearance). |
