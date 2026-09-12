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

## Verdict (2026-09-12 harvest-and-eval)

- Weights: v10 kernel CANCELLED after divergence; harvested unet_best.pt
  (ep4 gated pre-divergence best, 5.4MB, keys model/cfg/ep, e0 (32,1,3,3,3))
  + unet_last.pt (ep9, loss 2.5719, val_recall 0.000 — /tmp only, unevaluated).
  Evaluated BEST (gated) per hypothesis; ckpt thr=0.1 (not 0.3).
- Numbers (6bba t20–29, GT 8.4/frame; DoG same-window bar recomputed:
  recall 1.000, raw/adj 1.0, 44.4 det/frame): learned recall 0.9881 (83/84,
  exact gate-reduced Hungarian), edge raw/adj 0.0 (linking INFEASIBLE —
  count cloud percolates gated components; edges=[]), det/frame 26025
  (~3100x GT). Verdict: REJECT (fails all three gates).
- Infra: infer 3539s (~10min/frame, NMS-bound at thr 0.1); run.sh link+score
  OOM-killed (dense 26k Hungarian); staged scoring used identical
  _hungarian/_pair/edge_counts/division_counts math (see metrics.json notes).
  run.sh line 7 set to absolute WEIGHTS_PATH ($ROOT undefined at line 7).
- Decision: keep-trying (single-pass ceiling; v11 needs calibration/threshold
  + count-gated training that survives past ep4, not more capacity first).

## Decisions

- Window eval t20–29 on 6bba (dark sample); window-local scoring, no T_true.
- Single deterministic pass (ceiling keep-trying); verdict SIGNAL/REJECT.
