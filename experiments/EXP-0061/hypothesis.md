# EXP-0061 — UNet v11 gated-detection eval

## Hypothesis

v11 **gated** detections (threshold / top-K / density-capped — the v11
acceptance contract: calibration + count discipline that survives past the
v10 ep4 divergence) yield **edge_raw > 0 AND edge_adj > 0 on ≥ 1
sample/window** with **det/frame inside the usable band** (≤ ceiling below),
scored by the trusted scorer `scripts/score.py` v1.1.0 ONLY.

## Background

- `docs/PROTOCOL.md` §§2–6 (FROZEN v1.2): `cv_tag` discipline, nested-HP
  rule, promotion gates 1–5, BTE vs trusted standing only.
- Trusted standing (EXP-0053, log only): loso_worst **0.2092** / loso_micro
  **0.4826** / embryo_nested_worst **0.4193**. Historical 0.8194-class
  numbers are `tuned_ref` — never targets. Public diagnostic LB v7 gate-7
  **0.668** (slots 5 — do NOT submit; no kaggle calls at all).
- Negative control EXP-0035 (REJECT, read-only ref — see `notes.md`):
  v10 ep4 gated-best reached recall 0.9881 (83/84) at **26,025 det/frame**
  (~3100× GT 8.4/frame) → edge raw/adj **0.0** (linking INFEASIBLE,
  percolated components, edges=[]). DoG same-window bar: recall 1.000,
  raw/adj 1.0 at 44.4 det/frame. Count explosion is the disease; v11 must
  show count discipline, not just recall.
- v10 harvested+diverged; v11 train/infer is being rewritten in parallel by
  two other agents — this experiment touches NOTHING under `notebooks/`
  and is designed against the ACCEPTANCE contract, not their files.

## Falsification criteria (the bar — 2 lines)

- **PASS ("useful") iff: edge_raw > 0 AND edge_adj > 0 on ≥ 1 sample/window
  AND det/frame ≤ 500** (hard ceiling ≈ 11× the DoG window bar 44.4/f,
  ~60× GT 8.4/f; stretch-usable ≤ 100/f).
- **Else STOP with reason** (count-explosion repeat / edge-zero repeat /
  PENDING_CODE if v11 weights+infer never land) — no promotion content,
  no `trusted` claim, no re-tuning on the eval window.

## Tag discipline (HONEST per PROTOCOL v1.2 §2.2)

- `cv_tag` is a **learned-source, window-local** tag
  (e.g. `learned:unet-v11-gated:<sample>-<window>:signal-only`), explicitly
  **not** `trusted`, **not** `tuned_ref`, **not** `oracle`.
- Result can NEVER satisfy promotion gates 1–3; it is a signal check for
  the v11 "useful" acceptance only. Gating knobs (threshold/top-K/density
  cap) are fixed a-priori per the infer agent's contract — any re-tuning on
  the eval window would force a `tuned_ref` retag.
