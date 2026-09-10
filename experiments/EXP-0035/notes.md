# Notes — EXP-0035 Learned-detector evaluation

## Log

- Created via scripts/new_experiment.sh.
- 2026-09-10 (eval-builder): wrote notebooks/train_unet/infer.py (UNet
  verbatim from train.py; ckpt cfg + train-split-6bba mean/std 532.89/581.22;
  stride = half patch; thr 0.3; max-filter (3,9,9); NMS halves (1,4,4)).
  - Unit test `infer.py --self-test`: PASS (5/5 synthetic peaks, 2 decoys ignored).
  - Dry run `--random-weights` 6bba_05b6850b t20–21: completed in ~58 s,
    17209 nonsense detections (expected, random weights), edges [].
  - run.sh: empty WEIGHTS_PATH → exit 2 "weights not landed". Link+score
    plumbing validated on tiny synthetic det (BL.link 6 nodes → 3 edges;
    match_nodes/score_single OK; DoG t20–21 window recall recomputed 1.0).
  - Bars recomputed (score.py v1.1.0): 44b6 adj 0.9382/raw 0.9038/recall
    1.000; 6bba adj 0.8194/raw 0.7989/recall 0.893 (EXP-0009 convention).
  - No weights_eval numbers fabricated; metrics.json stays placeholder until
    unet_best.pt lands.

## Decisions

- Window eval t20–29 on 6bba (dark sample); window-local scoring, no T_true.
- Single deterministic pass (ceiling keep-trying); verdict SIGNAL/REJECT.
