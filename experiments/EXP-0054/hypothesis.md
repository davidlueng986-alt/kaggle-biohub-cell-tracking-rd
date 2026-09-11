# EXP-0054 — GT-free count target analysis (T_ratio vs edge)

## Hypothesis

A single GT-free COUNT-based operating target (detections/video vs a fixed
prior) predicts edge quality on hidden test, i.e. edge_raw peaks in a common
T_ratio interval across samples, so hidden-test operating discipline can be a
fixed count rule instead of per-sample tuning. Family: H-002/H-004 proxy problem
(no GT on hidden test).

## Background

- Scorer: `score = adjusted_edge_jaccard + 0.1*division_jaccard`, adjustment
  factor `(1 - 0.1*(T_pred-T_true)/T_true)` (docs/COMPETITION.md:72); T_true =
  `estimated_number_of_nodes` in GT `.geff` metadata (COMPETITION.md:28,55) —
  unobservable on hidden test.
- Prior rungs: per-embryo levels split by sample (EXP-0009/0010), descent
  overshoot (EXP-0011), splitter FP damage at T≈0.99 (EXP-0012), dark-sample
  @96 gains mixed (EXP-0039 GO / EXP-0040 MIXED / EXP-0043 DIVERGES), per-embryo
  levels failing on new samples (EXP-0021, STATE.md risks).
- Frozen per-sample rows harvested: EXP-0008/0009/0010/0011/0012/0021/0039/
  0040/0043/0044 → 13 unique detection-operating rows (6 samples × 1–3 ops).

## Falsification criteria

Target EXISTS iff best-T_ratio across samples falls in one interval narrow
enough to act on AND pooled det/frame predicts edge_raw at least as well as
T_ratio (Spearman_det ≥ Spearman_T) AND best-det/f spans <2×. Else NOT_EXISTS:
result = no count target beats per-sample tuning; hidden-test operating
discipline stays open.
