# GPU training design — EXP-0032 patches → learned detector + edge classifier

Design doc only. No training was run (CPU-only VM). Data ready at
`data/patches/` (6388 patches, 16×48×48 uint16, 50/50 pos/neg, 471 MB;
splits `44b6`/`6bba`; rows in `MANIFEST.csv`). Metric reference:
PROTOCOL v1.1 — `score = adjusted_edge_jaccard + 0.1·division_jaccard`,
7 µm per-timepoint match, voxel z=1.625/y=x=0.40625, sparse-aware edge FP,
`a=0.1` T_true penalty, division local-window ±1 tp.

## Option A (recommended first): 3D UNet heatmap detector
- Target: Gaussian heatmap (σ ≈ (1.5, 4, 4) vox ≈ ¼ cell radius) centred on GT
  nodes, rendered on the fly from manifest coords; background = 0.
- Net: 3D UNet, ~4 levels, 16 base channels (≈1–2 M params; fits T4 + 12 h).
- Loss: MSE on heatmap + Dice on binarised (heatmap > 0.5) mask.
- Inference: sliding window over full frames → peak detection (max-filter +
  threshold) → detections replace/augment DoG; link with standing causal
  Hungarian linker (`scripts/baseline_link.py`) + r10 fork gate.
- Why first: directly attacks the DoG recall ceiling on dark samples
  (EXP-0021/24); reuses the entire proven downstream stack.

## Option B: 2-tower patch classifier (detector reranker)
- Input: 16×48×48 patch → 3D CNN encoder (≈0.5 M params) → P(cell).
- Train on EXP-0032 pos/neg (BCE + label smoothing 0.1 — labels are noisy,
  see notes.md caveats); use as reranker on DoG candidates (kill FPs that
  inflate T_pred and edge-FP) or as second-stage scorer after Option A peaks.
- Cheap to train (<1 h); good diagnostic of whether learned appearance beats
  classical NCC (EXP-0015/16 margin was only 0.223).

## Option C (second stage): learned edge classifier
- Features per candidate edge (u@t → v@t+1): the two endpoint patches (A/B
  towers, shared weights) + geometric features (displacement in µm, Δintensity,
  size ratio). MLP head → P(link).
- Positives: GT edges (endpoint patches both GT-centred). Negatives: GT node
  paired with nearby non-linked detections + random cross-pairs within gate
  radius; keep 1:3 ratio, focal loss.
- Inference: replace Hungarian costs with −log P(link); keep causality
  (frames ≤ t only) and the r10 fork sub-gate (PROTOCOL §4.5: fork-count
  inflation without division gain = auto-reject).

## Metric alignment (how training choices map to the scorer)
- Optimise detection for 7 µm matching: heatmap σ and peak threshold tuned on
  trusted-scorer node recall, NOT on patch accuracy.
- T_pred discipline: the `a=0.1` inflation penalty punishes dense outputs —
  validate detection count ratio (T_pred/T_true ≈ 0.7–1.0, cf. EXP-0009) on
  holdout embryo before any linking experiment.
- Edge training must respect the sparse-aware FP rule: FPs only hurt at
  annotated targets — hard negatives must therefore be sampled near GT
  structures (bright-max share), not just random background.
- Division: do NOT train a fork predictor until edge Jaccard is stable; any
  fork head needs the division sub-gate (division-Jaccard gain + no edge
  regression, both folds).

## Anti-overfit (PROTOCOL v1.1 gates, no public-LB chasing)
- Embryo-grouped CV only: train on `6bba` patches → validate detection/linking
  via trusted scorer on holdout embryo `44b6` (fold0, promotion fold); then
  swap (fold1). Never sample-wise splits. Patches are pre-split by embryo.
- Embryo-balanced batches (6bba outnumbers 44b6 ~17:1 in patches); normalisation
  constants from train embryo only; ≥2 seeds for any reported win.
- Public LB is diagnostic only, observed after gates 1–3 pass. Division forks
  stay OFF until the edge model passes gates.
- Inference budget: profile per-video seconds on the full (100,64,256,256)
  volume; must fit ≈80–96 s/video on T4 (sliding-window UNet cost dominates —
  measure before committing to Option A at full resolution).
