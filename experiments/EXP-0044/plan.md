# Plan — EXP-0044 Image r10 forks on 6bba_05db0fb1 full video (3 GT divisions)

## Config / seeds

- Deterministic, CPU-only, no seeds (Hungarian + greedy proposal, sorted
  iteration). scipy assign backend (matches EXP-0021 row).
- Sample: 6bba_05db0fb1, t=0–99. Nodes: frozen EXP-0021
  `full_6bba_05db0fb1_t<0-99>.json` @98.5, global re-id (det files restart
  ids per frame → running gid across frames, t stamped from filename).
- GT: experiments/EXP-0003/gt/6bba_05db0fb1_gt.json (1229 nodes, 1183
  edges, 3 GT divisions, T_true 69800 — true T_true used in scoring).
- Arms: (a) base = `BL.link(graph)` gate-7 default; (b) fork =
  `FL.link(graph, propose_um=10.0)`, base_maxd default, isolation False
  (plain r10 rule).

## Steps

1. Cold rerun: `bash experiments/EXP-0044/run.sh` (< 25 min; link+score of
   ~26k-node dense graph, single pass).
   - 1/3: assemble nodes → base_pred.json + fork_r10_pred.json.
   - 2/3: `python3 scripts/score.py --pred <pred> --gt <gt>
     --out <scores>` per arm (true T_true from GT file).
   - 3/3: base-vs-fork table + verdict → metrics.json (exit 0 always).
2. Read verdict + deltas from metrics.json.

## Budget

CPU-only, single deterministic pass, well under 25 min (~4 min observed).
