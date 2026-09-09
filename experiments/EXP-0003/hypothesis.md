# EXP-0003 — Real-data oracle-linker baseline, subset 6 (H-001 + H-002 seed)

## Hypothesis

An oracle-detection (GT nodes) + causal per-pair Hungarian linker (7 µm,
causal, no training, no future frames) sets the honest real-data floor on
the 6-sample embryo-paired subset. Predictions: (a) edge Jaccard is high but
< 1.0 (real motion/ambiguity, unlike toy perfect 1.1); (b) division Jaccard
= 0 (linker emits ≤1 outgoing edge → zero forks → 4 GT-division FNs),
exercising the PROTOCOL division sub-gate; (c) 44b6-sparse vs 6bba-dense
samples differ (worst-fold matters, per §5). Embryo grouping respected:
scores reported per sample + per embryo, never pooled across embryos for
promotion. See `docs/PROTOCOL.md` v1.1 §§1–2/4–5.

## Falsification criteria

- REJECT the pipeline if any sample fails to score (missing T_true →
  non-promotable flag, not a crash), if edge TP+FP+FN weights are zero on a
  non-empty GT sample (weighting bug), or if a predicted fork appears
  (linker invariant violated → fix linker, re-run).
- `keep-trying` by default (baseline floor, not a model); `promote` only if a
  later variant beats this floor on fold0 (44b6) with no fold1 (6bba)
  regression across ≥2 seeds (§4 gates).
