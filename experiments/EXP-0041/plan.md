# Plan — EXP-0041 Window-best full-video validation 98.5/97.5

## Config / seeds

- Deterministic, CPU-only, no randomness (no seeds). Detector:
  `python3 scripts/dog_detect.py data/train/<sid>.zarr --t <T> --pct <P> --out
  <path>` with CLI defaults (== frozen DoG (1,3,3)/(1.6,5,5), min-size 50,
  percentile, downsample 1, truncate 4.0). Per-sample levels:
  44b6_0b24845f @ 98.5, 44b6_0c582fdc @ 97.5.
- Data (read in place, never copied): data/train/44b6_0b24845f.zarr,
  data/train/44b6_0c582fdc.zarr, all 100 frames (t=0..99) → 200 detections.
- GT: experiments/EXP-0003/gt/<sid>_gt.json (full sparse GT; true T_true
  32795 / 27958 carried in file, no override).
- Linker: baseline_link.link on globally re-identified nodes (det files
  restart ids per frame → reassign one gid per video, EXP-0021/EXP-0040
  pattern). Gate 7 µm default (image-side policy, not widened).
- Scorer: scripts/score.py v1.1.0 CLI verbatim
  (`python3 scripts/score.py --pred <pred> --gt <gt> --out <scores>`);
  scripts/* unmodified. Bars = fresh CLI rescores of frozen EXP-0040 @96.0
  preds (read-only). Full-video recall diagnostic (micro, over GT-annotated
  frames) via scipy linear_sum_assignment in the assembly step only
  (diagnostic, not part of the trusted score).

## Steps

1. Cold reproduce: `bash experiments/EXP-0041/run.sh` from repo root.
   run.sh per sample: (a) detect t=0..99 at the sample's level;
   (b) global gid re-id + BL.link → `<sid>_pred.json`;
   (c) score.py CLI vs full GT → `<sid>_scores.json`, plus CLI rescore of
   frozen EXP-0040 @96.0 pred → `<sid>_bar96_scores.json`;
   (d) assembly: recall diagnostic + HOLDS/BREAKS per criteria + GO/STOP,
   writes `metrics.json`.
2. Check metrics.json verdict + window-vs-full table.
3. No LB, no promotion, no git commits.

## Budget

~200 detections at ~0.6–1.1 s/frame ≈ 6–9 min + link/score; hard cap 35 min.
