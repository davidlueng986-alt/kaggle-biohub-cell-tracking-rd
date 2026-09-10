# Notes — EXP-0014 Scale fusion (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0014/run.sh` → exit 0, STOP recorded.
- Determinism check PASSED: config A reproduces EXP-0013 A bit-exactly
  (143/2/5) — pipeline deterministic across sessions, gating comparable.
- Window (t20–29 + t40–49, GT 167/148):
  - A baseσ@98.5: rec 0.982, raw 0.9533/adj 0.9804 (143/2/5).
  - B smallσ@98.5: rec 0.970, raw 0.8839 (137/7/11) — small scale alone
    fragments (worse recall AND worse edge).
  - C smallσ@98.0: rec 0.940, raw 0.8693 — worst of all.
  - D A∪novel-B: rec 0.988 (+1 GT node vs A), raw 0.9276 (141/4/7).
  - E A∪novel-small@98.0: rec 0.988, raw 0.9342 (142/4/6).
- D/E buy exactly +1 recall node for +2 FP / +1–2 FN — net edge down on
  both. Same leftover-confusion tax as the splitter: extra nodes near GT
  tracks confuse links more than recovered cells contribute. GO all False.

## Decisions
- `keep-trying` — STOP scale direction (single AND fused small-σ both lose
  on edge with readout). Standing policy unchanged: 44b6@99.0 + 6bba@98.5
  single-scale base (worst adj 0.8194).
- Dim cells remain the recall gap (6bba full-video 0.893). Remaining live
  directions: H-003 appearance-gated linking/disambiguation (use image
  content, not just geometry) or learned detector (needs GPU training —
  Kaggle-notebook territory, beyond this VM). Next: EXP-0015 appearance
  similarity probe (patch correlation around link endpoints — cheap,
  CPU, window-gated).
