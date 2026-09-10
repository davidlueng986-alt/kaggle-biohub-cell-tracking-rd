# Notes — EXP-0017 Gate ablation + gap pass (H-002/H-005)

## Log
- 2026-09-09: `bash experiments/EXP-0017/run.sh` → exit 0, all checks pass.
- Arm 1 (oracle, all 6): gate 7 reproduces floor exactly (sanity ✓).
  Gate 10: fold0 1.0933→**1.0998** (+0.0065, last 44b6 FN gone), fold1
  1.0705→**1.0884** (+0.0179; FNs 51→5 for FP cost of exactly 1 on
  05db0fb1); div sums identical [0,0,4] (neutral ✓ — one-to-one pairing
  cannot fork). Gate 14 == gate 10 (all fast pairs sit within 10 µm;
  14 dominated). → promotion CANDIDATE (both-fold win + div-neutral),
  pending EXP-0018 jitter replication (the r10 bar: ≥2 seeds).
- Arm 2 (image 6bba@98.5): gap pass adds ZERO edges (4229→4229) at both
  gates — correctly vacuous: DoG detects every frame (no chain breaks),
  and the 146 FNs are mismatches, not gaps. Gap-closing awaits true
  detection gaps (sparser operating points / dropout tracking).
  Gate 10 on dense graph: +2 TP / +9 FP → adj −0.0060 (HARMFUL) — clean
  asymmetry: widening helps clean oracle nodes, hurts dense image graphs.
- New scripts: `scripts/gap_link.py` (conservative t→t+2, fork-free by
  construction); `BL.link(gt, maxd=)` (default bit-identical floor).

## Decisions
- `keep-trying` — arm1 gate-10 is the first promotion CANDIDATE of the
  ladder (not a promotion: replication outstanding). Standing image policy
  unchanged (gate finding is oracle-side; image side rejects widening).
- Next: EXP-0018 jitter replication for gate-10 (EXP-0006 protocol:
  σ=0.3vox seeds {0,1,2} + noise-matched base + LOO). If it replicates,
  gate-10 promotes to new best (worst-fold 1.0884) with r10 re-scoped.
