# Plan — EXP-0017 Gate ablation + gap pass

## Config / seeds

- Protocol v1.1 frozen. Scorer v1.1.0. Deterministic.
- Arm 1 (oracle GT graphs, all 6): linker gate ∈ {7 (floor ref), 10, 14},
  adjacent-only. Embryo micros + div sums vs EXP-0003 floor.
- Arm 2 (image graph: EXP-0009 6bba@98.5 full pred, global ids): base gate
  ∈ {7, 10} × gap {off, on-conservative-14} (`scripts/gap_link.py`).
  Bar: @98.5 base adj 0.8194.
- Gap pass is fork-free by construction (unmatched sources only);
  `--allow-forks` is NOT tested (division sub-gate would apply — noted,
  deferred).

## Cold-run steps

1. `bash experiments/EXP-0017/run.sh` → `metrics.json` + verdict.
2. `bash scripts/run_loop.sh --dry-run`. Both exit 0.

## Budget

- CPU-only, minutes (graph ops; dense image pairs via scipy path).
