# Plan — EXP-0035 Learned-detector evaluation

## Config / seeds

- Protocol v1.1 frozen. Scorer scripts/score.py v1.1.0. Deterministic, CPU-only.
- Weights: `unet_best.pt` from notebooks/train_unet/train.py
  (patch_shape (16,48,48), patch_center (8,24,24), sigma_vox in ckpt cfg;
  embryo splits in MANIFEST.csv `split`: train=6bba, val=44b6).
- Inference: notebooks/train_unet/infer.py (ckpt cfg + train-split-6bba
  mean/std normalisation, stride = half patch, sigmoid ≥ 0.3,
  maximum_filter footprint (3,9,9), NMS halves (1,4,4)). Seed 0.
- Eval window: 6bba_05b6850b t20–29 (10 frames, dark sample).
  Linker: `import baseline_link as BL` (causal t→t+1 Hungarian, 7um) applied
  to detections in run.sh (global re-id across frames done by us, not infer.py).
- GT: experiments/EXP-0003/gt/6bba_05b6850b_gt.json (windowed to t20–29;
  window-local scoring, no T_true adjustment — T_true is full-video only).
- Bar: DoG window recall/edge recomputed from
  experiments/EXP-0009/full_6bba_05b6850b_pred.json on the SAME window
  (never pasted).

## Steps

1. Weights land → set `WEIGHTS_PATH` at top of `experiments/EXP-0035/run.sh`.
2. Run `./experiments/EXP-0035/run.sh`, which:
   a. infers the 10-frame window → det JSON (edges: []),
   b. links with BL.link → linked pred,
   c. windows GT + DoG reference to t20–29,
   d. scores learned vs GT and DoG vs GT (score_samples/score_single +
      match_nodes recall) → metrics.json + verdict.
3. Verdict rule: learned window recall > DoG window recall AND learned
   window edge score ≥ DoG window edge score AND counts ≤ 2× GT/frame
   → signal; else REJECT per hypothesis.md.

## Budget

- CPU-only. ~29 s/frame inference (measured dry-run) → ~5 min for 10 frames
  + linking/scoring (<1 min). Total < 10 min. Tiny validation only.
