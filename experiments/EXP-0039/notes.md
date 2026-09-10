# Notes — EXP-0039 05db0fb1 full-video @96.0 recall-vs-count-cost test

## Log

- Created via scripts/new_experiment.sh (EXP-0039 was free; EXP-0035/36/37/38
  exist).
- Calib single frame t=20 @96.0: 439 det, thr=133.4, elapsed 0.69 s
  (window prior ~450 det/frame confirmed).
- Detect loop 100/100 frames OK (~0.68 s/f).
- Link OK: 41987 nodes (globally unique ids), 35698 edges, assign=scipy,
  gate 7 um default, t coverage 0–99, per-frame 345–465 det.
- First link+score attempt with verbatim score.py hung past a 10-min timeout:
  root cause = score.py `match_nodes` uses a pure-Python O(N^3) Hungarian with
  N=max(n_pred,n_gt) per frame (≈450 here; ~1 s at N=268, worse at N=450,
  ×100 frames ×2 arms + recall loop). NOT a hang — just slow.
- Fix (no scripts/* edits): experiments/EXP-0039/score_fast.py imports the
  trusted scorer and, at RUNTIME ONLY, swaps `score._hungarian` for
  `scipy.optimize.linear_sum_assignment` (identical min-cost bipartite problem).
  Equivalence gate: identical total cost AND identical matched pairs on 8 real
  frames (t=0,20,50,99 × @96.0/@98.5) — all passed. Full score then took
  1.9 s + 0.8 s. scripts/score.py on disk unmodified.
- Baseline recompute: fresh `score_samples` run on frozen EXP-0021
  `6bba_05db0fb1_pred.json` reproduces the EXP-0021 row EXACTLY
  (raw 0.1969, adj 0.2092, ec 251/92/932) — confirms scorer path fidelity.
- run.sh re-validated cold end-to-end (detect→link→score→metrics.json).

## Decisions

- Verdict GO: recall up (0.6756 vs 0.2903, +0.3853) AND adj up
  (0.4822 vs 0.2092, +0.2730). Count cost does NOT win: sparse-aware FP rule
  ignores off-target detections (FP only 154 vs TP 620) while extra matches
  (841 vs 367 GT nodes) drive edge TP 620 vs 251.
- T_ratio @96.0 = 0.6015 (watch ~0.65; still under parity so the T-adjustment
  is a small bonus ×1.040, not a penalty).
- Division readout as expected: div 0.0, dc 0/0/3 both arms — one-to-one
  linker emits no forks; all 3 GT divisions FN.
- Timing: 0.68 s/frame @96.0 (vs 3.12 s/f @98.5 in EXP-0021 — note different
  machine conditions; both CPU-only).
- Follow-up: @96.0 is now the 05db0fb1 operating point; division-capable
  linker is the remaining gap (div term 0.0, 3 FN divisions).
