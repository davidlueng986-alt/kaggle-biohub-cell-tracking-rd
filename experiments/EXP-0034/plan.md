# Plan — EXP-0034 Per-sample-best transfer test

## Config / seeds
- Deterministic, CPU-only. No randomness, no seeds. Frozen DoG detector
  (scripts/dog_detect.detect — same code path as the CLI defaults):
  sig_small=(1.0,3.0,3.0), sig_large=(1.6,5.0,5.0), min_size=50,
  thr_mode=percentile, no peak-split, downsample=1, truncate=4.0.
- Per-sample levels (EXP-0024 best): 44b6_0b24845f@98.5,
  44b6_0c582fdc@97.5, 6bba_05db0fb1@97.5.
- Data (read in place, never copied): data/train/<sid>.zarr, all 100 frames
  (t=0..99), 3 samples → 300 detections.
- GT: experiments/EXP-0003/gt/<sid>_gt.json (full) with true T_true
  (estimated_number_of_nodes carried in the GT file; no override).
- Linker: baseline_link.link on globally re-identified nodes (detector emits
  per-frame ids restarting at 1 → reassign one gid per video, exactly as
  EXP-0021 run.sh does).
- Scorer: scripts/score.py v1.1.0 — full-video scores via the real CLI
  (`python3 scripts/score.py --pred <pred> --gt <gt> --out <scores>`);
  window-slice scores + recalls via score.score_samples / score.match_nodes
  in-process (identical code path, no CLI round-trip for slices).
- Window-implied edge definition: EXP-0024 was recall-only, so no
  pre-existing window edge level exists. The window-implied level is
  operationalised as the baseline_link-linked edge adj of the t=20..29
  slice of the same full-video detections, scored vs the window GT slice
  (nodes t∈[20,29], GT edges with both endpoints in-window, true full-video
  T_true). Rationale: same detector level, same linker, same T_true —
  isolates temporal transfer from level/linker/T_true confounds. Raw edge
  jaccard and |full_adj − window_recall| are recorded for transparency.

## Steps
1. Cold reproduce: `bash experiments/EXP-0034/run.sh` from repo root.
   run.sh calls `experiments/EXP-0034/transfer.py`, which per sample:
   a. detects t=0..99 at the sample's best pct (global gid re-id);
   b. links full video with baseline_link, writes `<sid>_pred.json`;
   c. scores full video with the score.py CLI vs full GT (true T_true),
      writes `<sid>_scores.json`;
   d. computes full-video micro recall via match_nodes;
   e. links + scores the t=20..29 slice in-process (window-implied edge);
   f. recomputes window recall from the same detections (determinism check
      vs EXP-0024 refs 0.80 / 0.50 / 0.4056);
   g. applies per-sample criteria (|Δrecall|≤0.10 AND |Δedge_adj|≤0.10 →
      TRANSFER-HOLDS else BREAKS) and the aggregate rule (3/3 → GO else
      STOP), writes `metrics.json`.
2. Check metrics.json verdict + per-sample window-vs-full table.
3. No LB, no promotion rung (probe only); no git commits.

## Budget
~300 detections, est. 8–15 min wall on CPU (EXP-0024 pace ~2 s/frame light
samples, ~4 s/frame dense 6bba; + linking/scoring). Hard cap 30 min.
Per-frame timings recorded in metrics.json.
