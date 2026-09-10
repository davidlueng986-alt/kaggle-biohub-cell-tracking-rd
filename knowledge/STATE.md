# STATE — cold resume in ≤5 min

Last updated: 2026-09-09 (PM GOLD: EXP-0020 denies combo promotion, best holds). Maintainer: gold-watch.
Prior: scorer v1.1 + EXP-0002 green. `PROMPT-RD-SYSTEM.md` done; active brief is `PROMPT-GOLD.md` (continuous gold run, PM owns go).

## Goal

Build a durable auto R&D loop (hypothesize → operationalize → execute → trusted score → update knowledge)
for Kaggle **Biohub – Cell Tracking During Development**, not a one-off notebook.

## Competition

- Slug: `biohub-cell-tracking-during-development` (code-competition).
- Page: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development
- Metric spec (normative): https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md
- Metric: `score = adjusted_edge_jaccard + 0.1 * division_jaccard` (per-timepoint 7 µm match, voxel z=1.625/y=x=0.40625, sparse-aware edge FP, `a=0.1` T_true penalty with T_true=`estimated_number_of_nodes`, division local-window ±1tp; micro-averaged; scores CAN exceed 1.0).
- Train: ~199 samples from **2 embryos only** (`6bba` ~128, `44b6` ~71) → embryo-grouped CV mandatory; frame-random splits leak. Format: OME-Zarr v3 `(100,64,256,256)` + `.geff` (`nodes/ids`, `nodes/props/{t,z,y,x}/values`, `edges/ids`); folders `{embryo}_{fov}`.
- Test: hidden, **embryo-disjoint** from train. Notebook-only submission, ≤12 h, no internet, ~80–96 s/video budget. Submission CSV: `id,dataset,row_type,node_id,t,z,y,x,source_id,target_id` (verified from sample_submission.csv 2026-09-09).
- Details: `docs/COMPETITION.md`. Deadline observed 2026-09-29 23:59 UTC (re-verify on competition page). Entry observed True, ~3287 teams, $60k (2026-09-09).

## Protocol pointer

- **FROZEN v1.1**: `docs/PROTOCOL.md` (faithful scorer v1.1.0: per-timepoint 7 µm Hungarian, pinned voxel, T_true=`estimated_number_of_nodes`, division window, submission.csv micro-average; embryo folds fold0 holdout `44b6` / fold1 holdout `6bba`; causality rule; 5 promotion gates; worst-fold ensemble; leakage checklist; compute budget).
- Competition facts: `docs/COMPETITION.md`. Auth steps: `docs/AUTH.md`.
- Loop runner: `bash scripts/run_loop.sh --dry-run` (script is `.sh`, takes no `--exp` flag).
- Scaffolder: `bash scripts/new_experiment.sh EXP-XXXX "title"`.
- Scorer `scripts/score.py` v1.1.0 + `scripts/test_score.py` (13 tests) — both must pass before any promotion. Legacy toy path kept for EXP-0001 hand-calc.
- Promotion gated on local trusted scorer + cross-fold stability; public LB is diagnostic only.

## Env

- Python 3.13.5 (verified `python3 --version`), **no GPU**, ~113 GB free. No full training on this VM.
- `requirements.txt`: `numpy>=2.0` only (no torch/scipy; GPU/Kaggle-notebook extras commented). No installs run by repo-hardener.
- `scripts/` contains: `score.py`, `run_loop.sh`, `new_experiment.sh` (no `run_loop.py` — correct any such reference to `.sh`).
- CI: `.github/workflows/smoke.yml` runs scorer dry-run + `run_loop.sh --dry-run` + guarded `test_score.py` (skips if absent) + JSON validation.

## Auth status (verification commands — re-run, do not assume)

- Kaggle CLI (`~/.local/bin/kaggle`): **WORKS (verified 2026-09-09 by repo-hardener: `kaggle competitions list --search "biohub"` exit 0, returned `biohub-cell-tracking-during-development`, userHasEntered=True)**:
  `export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"`
  then `kaggle competitions download -c biohub-cell-tracking-during-development -p data/` (requires Rules acceptance on competition page first).
- `gh`: **WORKS (verified 2026-09-09: logged in as davidlueng986-alt, remote HEAD in sync)**. Repo: https://github.com/davidlueng986-alt/kaggle-biohub-cell-tracking-rd (exists). Push frequent small commits.
- Subset download DONE 2026-09-09 (PROMPT-GOLD §1, after early-stop fix): 6 ids (3×44b6 + 3×6bba, embryo-paired), 738/738 files ok 0 fail, 2.6 GB in `data/` (gitignored). EDA needs `pip install zarr numcodecs` — DONE (zarr 3.3.0 on VM).
- Never commit secrets. See `docs/AUTH.md`.
- Never commit secrets. See `docs/AUTH.md`.

## What exists

- `docs/`: PROTOCOL.md (FROZEN v1.1), COMPETITION.md (submission schema + voxel + T_true verified 2026-09-09), AUTH.md.
- `scripts/`: score.py v1.1.0 (faithful), test_score.py (13 tests, all pass), run_loop.sh, new_experiment.sh. `requirements.txt` (numpy>=2.0).
- `experiments/EXP-0000/`: template; `run_loop.sh --dry-run` validates it.
- `experiments/EXP-0001/`: DONE — legacy toy harness re-scored under v1.1 (fold0 0.5/1.0/0.6 hand-calc match, `dry_run:true`, keep-trying). Do not recreate.
- `experiments/EXP-0002/`: DONE 2026-09-09 — full-scorer geometric validation (H-001+H-004): perfect 1.1 / idswitch 0.333 (FP≥1) / inflated adj 0.9 / division TP then FN; 6/6 checks pass; `dry_run:true`, keep-trying (no real data, NOT promotable).
- `experiments/EXP-0003/`: DONE 2026-09-09 — FIRST REAL-DATA result (H-001+H-002): oracle GT nodes + causal Hungarian linker on subset 6 → 44b6-micro 1.0933 / 6bba-micro 1.0705 / worst 1.0705; div 0/0/4 (no forks); `real_data:true`, keep-trying (floor, not a model). Helpers: `scripts/geff_to_graph.py`, `scripts/baseline_link.py`.
- `experiments/EXP-0004/`: DONE 2026-09-09 — fork-proposing variant (H-002+H-003, `scripts/fork_link.py --propose-um 15.0`): fold0 44b6 unchanged (+0.0000), fold1 6bba micro −0.0025, div sums 0/0/4→3/10/1. Sub-gate REJECT for promotion (edge regression on fold1; single-seed cap anyway). Signal kept: 3/4 GT divisions geometrically recoverable → EXP-0005 tighter gating.
- `experiments/EXP-0005/`: DONE 2026-09-09 — radius ablation {9,10,11,12}+isolation: r9 +0.0004 div 1/0/3; **r10 SELECTED** (+0.0011 fold1, div 3/0/1, FP=0, plateau r10==r11); r12 +0.0008 div 3/1/1; r15+iso −0.0011 div 4/7/0. fold0 identical grid-wide. Sub-gate numeric PASS; keep-trying (no fold0 win possible + single-run ceiling). r10 = ensemble-candidate.
- Submit path (GOLD §5, skeleton): `scripts/graphs_to_csv.py` (writer + `--check`; demo 4 subset preds → valid 4294-row CSV) + `notebooks/submission_skeleton.ipynb` (5 cells compile; demo wiring 15 nodes→12 edges OK) + `notebooks/README.md`. DRAFT — no submit yet; detector+weights TODO.
- `knowledge/`: this file + HYPOTHESES.md (H-001/H-002/H-004/H-005 active; H-003 classical parked, learned-features residual) + RESULTS.md (EXP-0000…0020 rows).
- `experiments/EXP-0006/`: DONE 2026-09-09 — r10 replication (H-002+H-003, `scripts/perturb_graph.py` σ=0.3vox × seeds {0,1,2} + noise-matched base arm + corrected same-set LOO): literal-identical FAIL (seed0 div 2/0/2; ±0.005 wobble is base-linker's, shared by both arms); refined PASS (variant≥base 18/18, FP=0 all seeds, LOO 6/6). r10 KEEPS ensemble-candidate; boundary-pair fragility → H-003 appearance case.
- `experiments/EXP-0007/`: DONE 2026-09-09 — DoG detection probe (H-002, `scripts/dog_detect.py`, CPU ~1s/frame): pct99 recall 1.00 both samples; 6bba mini-graph edge_raw 0.8462 (first meaningful image-based number); over video budget unoptimized (H-005 flag).
- `experiments/EXP-0008/`: DONE 2026-09-09 — full-frame sweep (H-002+H-005): 44b6 recall 1.000 edge_raw 0.9038 (strong); 6bba recall 0.835 (FALSIFIED <0.90 → pct99 dead for dense tissue; fix = level @98.5, threshold already per-frame). Curve monotone. Timing 2.05/0.84 s/frame (H-005 debt quantified). Infra: scipy fast path (floor bit-identical).
- `experiments/EXP-0009/`: DONE 2026-09-09 — full-video @98.5 (H-002): 44b6 adj −0.010 (raw identical — pure count cost) vs 6bba adj +0.107 (raw 0.7989, recall 0.893). Level SPLITS by sample → per-embryo levels (44b6@99.0 + 6bba@98.5) next; T_ratio 0.73–0.74 (bonus holds, crossover watched).
- `experiments/EXP-0010/`: DONE 2026-09-09 — combo + window probe (H-002): combo adj 0.9382/0.8194, worst 0.8194 ≥ both uniforms (all 4 combo checks pass); 6bba@98.0 window recall 1.000 det/f 57 → EXP-0011 full-video @98.0 GO. Standing image-based policy = per-embryo levels.
- `experiments/EXP-0011/`: DONE 2026-09-09 — full-video 6bba@98.0 (H-002): recall 0.880 + adj 0.8063, BOTH below @98.5 → descent OVERSHOT (merge-dominated: det/f +4% only, centroids displace past 7µm). STOP descending; 6bba locks @98.5 (recall 0.893, adj 0.8194). Lesson: gate windows must span density regimes.
- `experiments/EXP-0012/`: DONE 2026-09-09 — peak-splitter full-video (H-002, `dog_detect --split-size 3000`, 595 splits): recall 0.993 ✓ BUT adj 0.7088 ✗ (FP 30→168 — fragments link aggressively; T_ratio 0.99 parity, damage is edge-FP not T-penalty). Standing policy stays @98.5 base. Lesson: window gates need edge readouts, not recall alone.
- `experiments/EXP-0013/`: DONE 2026-09-09 — window gate t20–29+t40–49 (H-002; prominence 0.7 + two-phase conservative linking): A rec 0.982 raw 0.9533; D == C (phased engaged, NO stealing — leftover confusion). Gate FAIL → splitter family PARKED for linking; fewer-better detections win.
- `experiments/EXP-0014/`: DONE 2026-09-09 — scale fusion window (H-002; --sigma-small/large CLI; A==EXP-0013A exact determinism ✓): B/C worse alone; D/E buy +1 recall for +2FP (net edge down); GO all False → STOP scale direction. Standing policy stays single-scale @98.5 base.
- `experiments/EXP-0015/`: DONE 2026-09-09 — appearance probe (H-003, `scripts/appearance.py` NCC by scorer class, 4229 edges): TP 0.865 / FP 0.642 (margin 0.223 ✓, quartile bar missed by 0.003 ✗); ignored ≈ TP (sanity). Hard veto PARKED; soft weight GO (EXP-0016).
- `experiments/EXP-0016/`: DONE 2026-09-09 — soft-weight grid (H-003, `link_weighted`, anchor W0==A exact ✓): W=1–32 ALL identical (zero flips; shared-tissue patches carry zero marginal info). GO-by-equality overruled → H-003 classical PARKED. Debug lesson: detection id namespaces restart per frame (global re-id required). Standing policy unchanged.
- `experiments/EXP-0017/`: DONE 2026-09-09 — gate ablation + gap pass (H-002/H-005; `gap_link.py`, `BL.link maxd`): arm1 gate10 BOTH-fold win (+0.0065/+0.0179, FP+1, div-neutral) = first promotion CANDIDATE pending EXP-0018 replication; gate14 dominated. Arm2: gap vacuous (+0 edges, no chain breaks — mismatches≠gaps); gate10 harmful on dense graphs (−0.0060).
- `experiments/EXP-0018/`: DONE 2026-09-09 — gate-10 replication (H-002; jitter {0,1,2} + matched base + LOO): all seeds ≥ floor both folds + ≥ base, div 0/0/4 identical, FP==1, LOO clean → **PROMOTED** (worst 1.0884). Wider gate more robust under noise.
- `experiments/EXP-0019/`: DONE 2026-09-09 — gate-10+r10 combo (H-002/H-003; `fork_link base_maxd`, default path verified identical to frozen r10): fold0 identical (0 clean-tissue forks), fold1 1.0884→1.0895, div 0/0/4→3/0/1 (boundary pair recovered; FP stays 1). All 4 checks pass → promotion CANDIDATE pending EXP-0020 replication. Float-dust lesson: recompute bars from artifacts.
- `experiments/EXP-0020/`: DONE 2026-09-09 — combo replication (H-002/H-003; jitter {0,1,2} + matched gate-10 base + LOO): seed1/2 full pass; seed0 fold1 −4e-4 (div 2/0/2, predicted boundary flicker); safety perfect (FP==0 div, efp==1, LOO clean). Promotion DENIED, candidacy REVOKED (strict bar, narrow miss — as designed). LOO-iteration bug class fixed again (iterate shared set).
- `opencode-web.png`: local screenshot, git-ignored (not deleted).
- Subset download DONE 2026-09-09 (738/738, 2.6 GB in `data/`, gitignored). EDA deps installed (zarr 3.3.0 + numcodecs, CPU-only).

## Current best — PROMOTED 2026-09-09 (EXP-0018, pre-registered bar)

- **Gate-10 oracle links: worst-fold edge 1.0884** (44b6 1.0998 / 6bba 1.0884), div 0/0/4, FP+1 vs old floor. Replicated: all 3 jitter seeds ≥ floor both folds + ≥ matched base, div-neutral identical, FP==1, LOO clean. Wider gate MORE robust under noise.
- EXP-0019 CANDIDATE: gate-10+r10 combo, worst-fold 1.0895, div 3/0/1, fold0 identical (0 clean-tissue forks).
- EXP-0020 verdict: promotion DENIED (seed0 −4e-4), candidacy REVOKED per pre-registered rule — narrowly, as designed. Config retained in variant pool; re-nomination path = appearance-confirmed forks (jitter-invariant evidence).
- Superseded floor: EXP-0003 gate-7 (worst 1.0705) — kept for reference, no longer the number to beat.
- Standing IMAGE policy (submittable path): 44b6@99.0 + 6bba@98.5 (worst adj 0.8194) — image side rejected widening; oracle best is not submittable (needs GT nodes).
- r10: ensemble-candidate, re-scoped onto the new best (proposals validated on gate-7 links; combination untested).
- Harness (toy): EXP-0001 0.600/0.333; EXP-0002 perfect 1.1, idswitch 0.333.
- Next: EXP-0021 image-policy transfer — per-embryo levels (44b6@99.0 + 6bba@98.5) across all 6 subset samples + link + embryo micros (H-002; tests level transfer within embryo); first serious submit only after local gates + timing headroom.

## Next loop steps (cold agent — copy/paste)

```bash
cat knowledge/STATE.md knowledge/HYPOTHESES.md knowledge/RESULTS.md
cat docs/PROTOCOL.md docs/COMPETITION.md docs/AUTH.md PROMPT-GOLD.md
ls experiments/ data/train/
# Auth checks (both WORKS 2026-09-09):
export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"
gh auth status
# Download watch: tail -n 5 /tmp/biohub-subset-dl.log  (expect DONE ok 738 fail 0)
# Loop (EXP-0001…0020 done — read them, don't recreate):
bash scripts/run_loop.sh --dry-run
python3 scripts/score.py --dry-run
python3 scripts/test_score.py
# New experiment (EXP-0021 image-policy transfer, H-002):
bash scripts/new_experiment.sh EXP-0021 "<title>"
```
