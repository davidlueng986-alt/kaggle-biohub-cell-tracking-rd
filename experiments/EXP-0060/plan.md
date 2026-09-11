# Plan — EXP-0060 Sign-corrected nested binary-brightness rule (HIGH-B→96)

## Config / seeds

- Deterministic (no seeds): DoG detector CLI defaults, Hungarian linker
  gate 7.0, scorer v1.1.0. HP rule fixed a priori (hypothesis.md).
- Data: data/train 6 samples, full video (100 frames each).
- CV: LOSO over 6 samples (fit-median on other 5) + embryo-nested both
  directions (fit-median on fit embryo, apply to held-out embryo).
- Brightness B(S): frame-mean intensity t20–29, recomputed fresh here
  (60 frame reads; expected identical to EXP-0059/brightness.json).

## Steps

1. `python3 brightness.py` — recompute B(S), derive nested assignments
   (sign-corrected: HIGH-B→96.0 / LOW-B→99.0), write brightness.json.
   Expected (from EXP-0059 B values):
   LOSO: 0113de3b@99, 0b24845f@96, 0c582fdc@96, 05b6850b@99,
   05db0fb1@96, 062c8d37@99.
   Nested fit-44b6→6bba: 05b6850b@99, 05db0fb1@96, 062c8d37@99.
   Nested fit-6bba→44b6 (median 85.89): ALL of 0113de3b/0b24845f/0c582fdc@96.
2. `python3 detect_missing.py` — fresh-detect missing combos (cap 200f):
   6bba_062c8d37@99 (100f) + 44b6_0113de3b@96 (100f). NOTE: the pre-reg
   brief named only 062c8d37@99 as missing, but the corrected nested arm
   fit-6bba→44b6 assigns 0113de3b@96 (B=256 > fit-median 85.89), which was
   never detected (EXP-0059 omitted it over its 300f cap). Both fit in the
   200f cap. All other combos reuse frozen artifacts (manifest in
   link_score.py; 100f each, verified by assert).
3. `python3 link_score.py` — link (BL.link gate 7, global gid
   reassignment) + score (score_samples v1.1.0; runtime-only scipy
   Hungarian swap after equivalence gate; scripts/* untouched). Writes
   pred_*.json, scores.json, metrics.json (cv_tag trusted + per-fold HP
   provenance + verdict vs BTE).
4. Run `./experiments/EXP-0060/run.sh` (steps 1–3 in order; exits 0,
   verdict in metrics.json).

## Budget

CPU-only, deterministic. Fresh frame-detections: exactly 200 (at the
≤200 cap). Brightness probes: 60 frame reads (not detections).
Link+score: 7 combos, seconds. Total ~5 min.
