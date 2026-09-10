# Plan — EXP-0027 Detection-internals profile

## Config / seeds
- Deterministic, CPU-only, no seeds (fixed percentile/label ops).
- Params: pct=98.5, min_size=50, max_size=50000, split_size=None (no split),
  SIG_SMALL=(1.0,3.0,3.0), SIG_LARGE=(1.6,5.0,5.0) imported from scripts/dog_detect.
  NOTE: mission pct=98.5 used; dog_detect.py CLI --pct default is 99.5.
- Frames: data/train/6bba_05b6850b.zarr + data/train/44b6_0113de3b.zarr, t=20..24 (read-only arr[t]).

## Steps
1. `python3 experiments/EXP-0027/profile_detect.py --out experiments/EXP-0027/metrics.json`
   (or `./experiments/EXP-0027/run.sh`). Replicates detect()'s exact calls with
   perf_counter timers; scipy warmed up outside timed region; fidelity gate asserts
   staged node list == DD.detect() nodes and thr match every frame.
2. Inspect per-stage means/shares + projections in metrics.json.
3. No quality scoring (timing-only; zero method change — implement nothing).

## Budget
< 15 min (actual: ~1 min for 10 frames + warmup + cross-checks).
