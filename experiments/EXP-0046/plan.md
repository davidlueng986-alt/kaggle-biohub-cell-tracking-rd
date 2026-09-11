# Plan — EXP-0046

1. Scaffold EXP-0046 (free id verified: no EXP-0046 in experiments/).
2. Implement experiment-local `orphan_pass.py` (no shared-script edits):
   global gid re-id, base = `baseline_link.link` gate-7, orphan second-edge
   pass per mission spec (10um, incoming-less w, outdeg(u)==1, nearest-only).
3. `run.sh`: base+pass per sample, score both vs full GT with `score.py`
   logic (true T_true from GT), write `metrics.json` + verdict.
4. Verify: base reproduces frozen EXP-0021 edges; determinism re-run;
   geometric check that any div TP sits at the audited site.
5. Write `notes.md` + `metrics.json` (base-vs-pass table per sample + verdict).
   GO -> recommend EXP-0047 replication only. STOP -> park rule.

Scope: CREATE under experiments/EXP-0046/ only. No edits to scripts/*,
docs/*, knowledge/*, other experiments/*; no pip installs; no kaggle calls;
no git commits/pushes. CPU-only, deterministic.
