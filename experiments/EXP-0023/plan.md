# Plan — EXP-0023 Full-video DS both samples

## Config / seeds

- Deterministic, CPU-only, no training, no randomness.
- 44b6_0113de3b @pct 99.0 + 6bba_05b6850b @pct 98.5 (frozen operating points),
  `--downsample 2`, t=0..99 (100 frames each, 200 detections).
- Linker: baseline_link causal adjacent-frame Hungarian, gate 7um, global
  re-id per video (det files restart ids per frame).
- Scorer: scripts/score.py v1.1.0 vs experiments/EXP-0003/gt/<sid>_gt.json
  (true T_true). References recomputed from EXP-0008/EXP-0009 artifacts.

## Steps

1. Run `./experiments/EXP-0023/run.sh` (detect -> link -> score -> metrics.json).
2. Inspect `metrics.json` checks + verdict (GO/STOP).
3. Record outcome in `notes.md`; no promotion (single deterministic run).

## Budget

< 30 min CPU. Observed: detect ~45 s (44b6) + ~23 s (6bba); link+score ~1-2 min.
