# Notes — EXP-0038 T-discipline track filter

## Result: FAIL → STOP (park filtering)

Gate (worst-of-2, scorer v1.1.0, true T_true): adj gain >= +0.02 AND
recall loss <= 0.005 AND FP down, per sample.

| sample | before (raw/adj) | after (raw/adj) | d_adj | recall before→after | edge-TP loss | FP |
|---|---|---|---|---|---|---|
| 6bba_05b6850b | 0.7989 / 0.8194 | 0.7906 / 0.8160 | **-0.0035** | 0.8791→0.8560 (**-0.0232**) | 8/699 = 1.14% | 30→29 ✔ |
| 6bba_05db0fb1 | 0.1969 / 0.2092 | 0.1635 / 0.1751 | **-0.0341** | 0.2986→0.2229 (**-0.0757**) | 44/251 = 17.5% | 92→83 ✔ |

- Adj-gain bar: FAIL both (worst-of-2 = -0.0341, bar needs >= +0.02).
- Recall bar: FAIL both (-0.0232, -0.0757 vs <= 0.005 allowed loss).
- FP-down bar: PASS both (-1, -9), but insufficient alone.
- Division Jaccard unchanged (1.0 / 0.0); div counts untouched (no forks
  removed/added that matter: 0/0/0 and 0/0/3 before and after).
- T_ratio moved AWAY from 1 (0.7424→0.6793; 0.3749→0.2929): both graphs
  already under-predict vs T_true, so dropping dets only enlarges the
  under-prediction (the a=0.1 factor grows slightly but raw loss dominates).

## Why it failed (mechanism)

The reference assumption ("short tracks in dense graphs are FP junk") does
not transfer: our linker fragments true cells into short tracks, so
min-len-6 deletes matched GT nodes/edges. Evidence: on 05db0fb1 GT-node
recall collapses 367→274 matched and edge TP falls 251→207 (-17.5%) while
FP falls only 92→83 — the filter removes ~5× more TP edges than FP edges.
On 05b6850b the damage is smaller (TP -8, FP -1) but still net-negative.
Count discipline is not our binding constraint here (both T_pred < T_true);
link quality/recall is. The Lineage Forge reference presumably links
cleanly enough that its short tracks are pure noise — ours are not.

## Filter audit (deterministic)

- Components: 05b6850b: 494 (222 kept, 272 dropped incl. 115 isolated);
  05db0fb1: 4503 (1486 kept, 3017 dropped incl. 1248 isolated). Zero
  dangling edges in both. Isolated-node pass fully subsumed by (a), as
  designed. Rescue hit budget exactly (205/205, 973/973 nodes; 46/195
  tracks, longest-first) — re-added tracks still could not cover the
  recall hole, confirming the loss sits in tracks of length <= 5 that the
  cap correctly refuses to fully restore.

## Follow-ups (parked, not pursued here)

- Do NOT promote min-len filtering of frozen dense graphs.
- If revisited: score-gated rescue (needs per-det confidences, which the
  frozen graphs lack), or shorter min-len (2–3) ablation, or fix the linker
  fragmentation first (short tracks are a linking symptom, not a detection
  symptom). Any revisit = new EXP id; this dir stays frozen as the FAIL
  record.
