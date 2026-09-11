# Notes — EXP-0049 Drift re-audit submit_gold after GATE_UM 7.0 + find_wheels edits

## Log
- Scaffolded via `scripts/new_experiment.sh EXP-0049` (EXP-0048 already taken → next free id).
- Ran `./experiments/EXP-0049/run.sh` → all 9 checks PASS, verdict IN-SYNC (~9 s).
- READ-ONLY audit: no edits to `scripts/*`, `docs/*`, `knowledge/*`, `notebooks/*`,
  or other experiments; no pip installs; no kaggle calls; no git commits.

## Decisions
- Core cell exec'd with stub constants matching notebook env cell
  (VOXEL=(1.625,0.40625,0.40625), SIG (1,3,3)/(1.6,5,5), MIN_SIZE=50, GATE_UM=7.0).
- Repo `detect()` called with defaults (pct per case; min_size 50, no split) —
  matches notebook `detect_frame` semantics (vectorized center_of_mass, min-size only).
- Link comparison uses frame-major global re-id on both sides so edge ids correspond.
- Minor cosmetic note (not drift): kernel-metadata title still says "gate-10"
  while config is 7.0; harmless but could be renamed on next submit edit.

## Results
- detect: 6/6 frames equal (6bba n=43/44/41; 44b6 n=146/151/151).
- link: both chains equal (6bba 84 edges; 44b6 281 edges).
- assign: N=70 scipy path identical perm (cost 14.410420); N=5 pure path identical.
