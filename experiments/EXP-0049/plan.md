# Plan — EXP-0049 Drift re-audit submit_gold after GATE_UM 7.0 + find_wheels edits

## Config / seeds
- Data: `data/train/6bba_05b6850b.zarr` + `44b6_0113de3b.zarr`, frames t20–22.
  GT not needed (equivalence only, no scoring).
- Seeds: `random.Random(0)` for the N=70 assign cost matrix. CPU-only, deterministic.
- Repo: `/home/box/workspace/kaggle-biohub-rd`. NOTE: EXP-0048 was already taken,
  so this audit uses the next free id EXP-0049.

## Steps
1. Static checks: GATE_UM count (exactly one `= 7.0`, zero `10.0`), `find_wheels`
   present with no hardcoded wheels path, all code cells `ast.parse`, kernel-metadata
   flags (gpu false, internet false, dataset+competition sources), pct map + no forks.
2. Exec notebook core cell (cell 3) in isolation with stub constants
   (`np`, VOXEL, SIG_SMALL/LARGE, MIN_SIZE, GATE_UM); compare vs repo on identical inputs:
   a. detect positions EQUAL on 6 frames (6bba t20–22 @98.5, 44b6 t20–22 @99.0).
   b. linked edges EQUAL on both 3-frame chains at maxd=7.0 (frame-major re-id both sides).
   c. assign EQUAL incl scipy path (one N=70 cost matrix vs `BL._assign`; bonus N=5 pure path).
3. Run `./experiments/EXP-0049/run.sh` (calls `probe.py`, writes `metrics.json`).
4. Verdict DRIFTED on ANY behavioral inequality (list it); IN-SYNC otherwise.

## Budget
CPU-only, < 20 min (actual ~9 s for probes).
