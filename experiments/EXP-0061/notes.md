# Notes — EXP-0061 UNet v11 gated-detection eval

## Log

- Created via `scripts/new_experiment.sh EXP-0061 "UNet v11 gated-detection eval"`.
- Scaffolded 2026-09-13 as PENDING_CODE: v11 train/infer owned by two
  parallel agents; `notebooks/` never touched (probed read-only by run.sh).
  `docs/PROTOCOL.md` §§2–6 read first; scorer pinned v1.1.0; PROTOCOL v1.2.
- `ls experiments/` confirmed EXP-0061 vacant (tail: …EXP-0059, EXP-0060).
- `knowledge/RESULTS.md` tail read for row format; NOT edited (orchestrator
  merges).

## Negative control — EXP-0035 failure signature (read-only reference)

Verified by reading `experiments/EXP-0035/notes.md` + `metrics.json`
(nothing modified there):

- Weights: v10 `unet_best.pt` ep4 gated pre-divergence best (5.4 MB);
  `unet_last.pt` ep9 diverged (loss 2.5719, val_recall 0.000) — unevaluated.
- Window: `6bba_05b6850b` t20–29, window-local scoring, no `T_true`;
  GT 8.4/frame; ckpt thr=0.1 (not 0.3); infer 3539 s (~10 min/frame,
  NMS-bound); link+score OOM-killed on dense 26k Hungarian → staged scoring
  with identical `_hungarian`/`_pair`/edge/division math.
- Learned: recall **0.9881** (83/84, exact gate-reduced Hungarian),
  **det/frame 26,025** (~3100× GT), edge_counts TP 0 / FP 0 / FN 74,
  **edge raw/adj 0.0** (linking INFEASIBLE — count cloud percolates gated
  components; edges=[]). Verdict: **REJECT** (fails all three gates).
- DoG same-window bar (recomputed): recall 1.000, raw/adj 1.0,
  44.4 det/frame.
- Lesson for v11: recall without count discipline is worthless. Hence the
  EXP-0061 bar requires edge/adj > 0 **jointly with** det/frame ≤ 500
  (hard ceiling ≈ 11× DoG 44.4/f; stretch-usable ≤ 100/f).

## Decisions

- Ceiling 500/f chosen as falsifiable and anchored: an order of magnitude
  above the DoG operating point but 50× below the EXP-0035 explosion, so a
  repeat of the failure signature unambiguously STOPs.
- `cv_tag` will be learned-source window-local signal-only — HONEST per
  PROTOCOL §2.2 (no `oracle`, no `tuned_ref`, never promotable via gates
  1–3). Gating knobs fixed a-priori; any eval-window tuning forces retag.
- Trusted standing cited log-only (loso_worst 0.2092 / micro 0.4826 /
  nested_worst 0.4193, EXP-0053); 0.8194/0.946-class numbers never targets.
- No pip installs / kaggle calls / commits performed by scaffold.
