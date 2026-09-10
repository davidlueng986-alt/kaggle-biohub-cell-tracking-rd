# EXP-0029 — Truncated gaussians + kernel upgrade prep (H-005)

## Hypothesis

Truncating DoG kernels (radius 4σ→2σ) buys ~1.5× on filtering (~0.1 s/f)
at zero detection change: window positions EQUAL to frozen A, recall
equal, linked edge equal (143/2/5). Single-frame probe already shows
identical sets (45 nodes, 8/8) with gauss 0.36→0.24 s. Gate: positions
equal on all 20 window frames AND edge equal AND speedup ≥1.1× → adopt
truncate=2.0 as a VALIDATED OPTION (default stays 4.0 for frozen
comparability; kernel passes it explicitly). Then kernel upgrade: notebook
detect_frame gets vectorized centroids (+ truncate=2.0), push v6, visible
COMPLETE + timing vs v5's 0.36 h. NO leaderboard submit (2 slots; PM rule).
Ceiling keep-trying (infra rung).

## Falsification criteria

- REJECT truncate=2.0 on ANY position mismatch or edge difference
  (truncation artifacts matter → stay at 4.0, pay full filter cost).
