# Plan — EXP-0031 Image-side fork proposals

## Config / seeds
- Deterministic, CPU-only, no seeds (pure-python + scipy Hungarian paths are exact).
- Sample: 6bba_05b6850b; frames t20-29 + t40-49 (20 frames).
- Frozen inputs: experiments/EXP-0013/A_t{t}.json (@98.5 detections, ids restart per
  frame -> global re-id in run.sh, same construction as EXP-0013 reference A).
- GT subgraph: experiments/EXP-0003/gt/6bba_05b6850b_gt.json filtered to window,
  T_true scaled x20/100 (=1272).
- Link: `fork_link.link(nodes, propose_um=10.0)` with default gate-7 base
  (r10-on-gate7 only; do NOT pass base_maxd).
- Score: trusted scorer scripts/score.py v1.1.0 via score_samples (single sample).

## Steps
1. `bash experiments/EXP-0031/run.sh` (cold-runnable; rebuilds window graphs, links
   BL baseline + r10 fork, scores both, applies gate, writes metrics.json).
2. Read verdict from experiments/EXP-0031/metrics.json (`decision` + `gate` block).
3. PASS -> GO full-video image-fork test (recommend EXP-0034, do NOT run here);
   FAIL -> STOP (park image forks).

## Budget
CPU-only, < 20 min (actual: seconds; 911 det nodes / 167 GT nodes window).
