# EXP-0035 — Learned-detector evaluation

## Hypothesis

A trained 3D-UNet heatmap detector (train.py, 1.36M params, embryo-grouped
CV train=6bba/val=44b6), run through `notebooks/train_unet/infer.py`
sliding-window inference + `baseline_link` causal linking, beats the frozen
DoG operating points on the dark sample **6bba_05b6850b** with controlled
counts (detections/frame within 0.5–1.5× GT density, no count explosion):

- Bar (RECOMPUTED via scripts/score.py v1.1.0 on reference preds, not pasted):
  - 44b6_0113de3b @99.0 (EXP-0008 ref): recall 52/52 = **1.000**,
    raw edge jaccard **0.9038**, adjusted **0.9382**.
  - 6bba_05b6850b @98.5 (EXP-0009 ref): recall **0.893** (EXP-0009
    detection-recall convention; scorer window match 757/861),
    raw edge jaccard **0.7989**, adjusted **0.8194**.
- Predicts: on the 6bba_05b6850b t20–29 window, learned detection recall
  (score.py `match_nodes`, 7um gate) EXCEEDS the DoG window recall recomputed
  from the EXP-0009 reference on the same window, with per-frame counts
  within 2× of GT and window edge score ≥ DoG window edge score.

## Falsification criteria

- REJECT if, on the frozen 10-frame window with landed `unet_best.pt`,
  learned recall ≤ DoG window recall OR counts explode (>2× GT/frame) OR
  window edge score < DoG window edge score. Then the learned detector at
  this capacity/training is dead for dark samples → new hypothesis needed
  (threshold/calibration, more capacity, or better negatives).
- Ceiling keep-trying: single deterministic pass, CPU-only. No gate impact
  either way at this rung; promotion needs local win + replication per
  PROTOCOL. Public LB is diagnostic only.
