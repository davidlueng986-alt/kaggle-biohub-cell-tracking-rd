# Plan — EXP-0061 UNet v11 gated-detection eval

## Config / seeds

- Deterministic single pass, seed pinned by the infer agent's contract
  (record actual seed in `metrics.json` when run); CPU-only.
- Eval window (default, matches EXP-0035 control): sample `6bba_05b6850b`,
  frames t20–29, window-local scoring, no `T_true` (same convention as the
  negative control so the comparison is apples-to-apples).
- Gating knobs (fixed a-priori, NOT tuned on the eval window): detection
  threshold / top-K per frame / density cap — values taken from the v11
  infer agent's acceptance contract; record verbatim in `metrics.json`.
  Overrides via env: `V11_THRESHOLD`, `V11_TOPK`, `V11_DENSITY_CAP`.
- Scorer: `scripts/score.py` v1.1.0 ONLY (`--dry-run` must pass;
  `scripts/test_score.py` 13 tests must pass before any number is trusted).

## Steps

1. Cold check: `./experiments/EXP-0061/run.sh` — it probes for v11
   weights (`data/weights/unet_v11*.pt` or `$V11_WEIGHTS`) and the v11
   infer entrypoint (`$V11_INFER` or the parallel agents' contract path).
   `notebooks/` is NEVER modified by this experiment (read-only probe).
2. If weights+infer exist: run gated infer → link (same linker math as
   EXP-0035 staged scoring) → score predictions with trusted
   `scripts/score.py` → apply the 2-line bar → write real numbers into
   `metrics.json`.
3. If either is missing: `run.sh` exits cleanly with status PENDING_CODE —
   it validates scorer plumbing (`score.py --dry-run`) and records
   `status` + `reason` in `metrics.json`. NO numbers are fabricated.
4. Compare against the EXP-0035 negative control in `notes.md`
   (26,025 det/frame → 0.0); verdict PASS/STOP per `hypothesis.md`.
5. Do NOT edit `knowledge/RESULTS.md` (orchestrator merges); report the
   ready-to-append row text in the deliverable instead.

## Budget

- CPU-only, deterministic, < 30 min wall-clock for the scaffold path
  (scorer dry-run ≈ seconds). A full gated-infer run inherits the v10
  timing caveat (EXP-0035 infer ~3539 s NMS-bound at thr 0.1) — record
  `infer_s_per_video` in `metrics.json`; any run exceeding the per-video
  budget is marked non-submittable per PROTOCOL §7. No pip installs, no
  kaggle calls, no git commits/pushes.
