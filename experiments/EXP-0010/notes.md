# Notes — EXP-0010 Combo + window probe (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0010/run.sh` → exit 0, all 5 checks pass.
- Combo (44b6@99.0 + 6bba@98.5, re-scored frozen arms): per-sample adj
  0.9382 / 0.8194; worst-fold 0.8194 ≥ uniform99 (0.7121) and ≥ uniform98.5
  (0.8194, tie on the binding sample). Gain over uniform98.5 sits on 44b6
  (+0.0101); gain over uniform99 sits on 6bba (+0.1073). No sample pays for
  another's level — per-embryo levels strictly justified on current evidence.
- Window 6bba@98.0 t0–9: recall **1.000**, det/f 57 (vs ~47 @98.5, modest
  +21% count growth). Descent continues → EXP-0011 full-video @98.0 is
  GO (cheap gate passed before committing ~8 min full video).

## Decisions
- `keep-trying` — assembly + probe rung (single deterministic pass ceiling).
  Combo (per-embryo levels) becomes the standing image-based policy to beat;
  oracle floor remains the overall reference (1.0705 worst-fold).
- Next: EXP-0011 full-video 6bba@98.0 (+44b6 control re-affirm not needed —
  44b6 level already locked @99.0 with recall 1.000; run 6bba only).
