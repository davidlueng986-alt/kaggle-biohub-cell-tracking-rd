# STATE — cold resume in ≤5 min

Last updated: 2026-09-11 (STAGE A: 0040 MIXED, UNet slow ~1.25h/ep timeout risk; LB pending). Maintainer: gold-watch.
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

## Submit log (PM override 2026-09-10: LB as diagnostic, first serious attempt)

- Kernel: https://www.kaggle.com/code/liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10 (v4 COMPLETE on visible data).
- Stack: per-embryo DoG (44b6→99.0, 6bba→98.5, unknown→98.5) + gate-10 links, NO forks (safety; r10 unpromoted). Offline: numpy/scipy (preinstalled) + zarr/numcodecs via `biohub-zarr-wheels` dataset (`vendor/wheels/README.md` recipe; `*.whl` git-ignored).
- Visible output: 112,599 rows / 4 datasets, kernel-side validation passed (consecutive ids, refs resolve, full coverage); local re-check sane. Total 0.29h (~261 s/video on Kaggle CPU).
- Debug trail: v1 zarr-missing (fail-fast worked) → wheels dataset; v3 wrong mount path → discovery prefers `test/`; v4 green.
- ✅ SUBMITTED 2026-09-10 via CLI (PM gold-watch): kernel v5 CPU (`enable_gpu=false`; v4 P100 blocked by competition). ref `56143782`, status PENDING hidden rerun. publicScore DIAGNOSTIC only when scored. Kernel: https://www.kaggle.com/code/liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10
- ➕ Agent duplicate submits 12:06 UTC: refs `56143803` + `56143804` (same v5; CLI success output showed only remaining-count, so a verify re-run double-submitted — SLOT INCIDENT, agent error: 5→2 remaining today. Rule: check `submissions` list BEFORE any resubmit; remaining-count output = success, stop). All three PENDING; PM's 56143782 is the primary watch ref.
- CPU kernel v5 log: visible 4 videos, valid 112,599-row CSV, **0.36 h total (~324 s/video)** — worse than v4's 0.29 h; hidden projection ~18 h vs 12 h cap → TIMEOUT RISK now primary (H-005 paydown urgent regardless of score).
- ⚠️ RISKS for hidden rerun: (a) timing — 261 s/video projects ~14.4 h over ~199 videos vs 12 h cap (H-005 must pay down if the run times out); (b) transfer — EXP-0021 found per-embryo levels fail on 3/4 new samples (fallback @98.5 on unseen embryos is suspect; LB diagnostic arbitrates); (c) gate-10 on image graphs was −0.006 on one dense sample (EXP-0017 arm2).
- publicScore: **0.650** COMPLETE on refs `56147475` (v6) + `56143782`/`803`/`804` (v1) — all COMPLETE 2026-09-10. Same-account notebook `biohub-lineage-forge-precision-tracking` ref `56144839` COMPLETE publicScore **0.946** (was mislabeled "not ours" in earlier watch; same user liangwanyiudavid). Gold DoG path not gold-zone; Lineage Forge is much closer to leaderboard (~0.97). Slots exhausted Sep-10 UTC (5 submits); next gate-7 submit after midnight UTC reset.
- GATE VERDICT (visible, 2026-09-10): probe kernel `biohub-probe-gate7-image` v3 COMPLETE — gate-7 beats gate-10 on ALL FOUR visible samples (0113de3b adj 0.6606→**0.9382**; others +0.002/+0.006/+0.017; 109,761 rows). submit_gold flipped to gate-7, v7 COMPLETE 0.12 h valid — RECOMMENDED next leaderboard submit after slot reset. Oracle gate-10 best (1.0884) stands separately (sparse-graph regime). Debug lesson: verify notebook edits on disk before push (one no-op patch cost a wasted version).
- TIMEOUT STORY REVISED: v6 hidden rerun COMPLETED + scored → hidden fits in 12 h (18 h fear falsified; v6 output covered hidden test). Timing still worth improving (denser hidden mixes unknown) but no longer primary.

## GPU training watch (Stage A parallel output, 2026-09-10)

- Dataset: `liangwanyiudavid/biohub-train-patches` READY (450 MB: 44b6/6040-row 6bba patches.npy + MANIFEST.csv; md5-verified). Recipe: EXP-0032.
- Script: `notebooks/train_unet/train.py` (1.36M-param 3D-UNet heatmap, torch/numpy/stdlib only, CPU-smoked locally, embryo-balanced batches + HNM, ckpts per improvement) + kernel-metadata (GPU on, internet off).
- Kernel: https://www.kaggle.com/code/liangwanyiudavid/biohub-unet-train-v1 — v1/v3 mount-path fail (fixed with layout-robust search) → v4/v5/v6 diagnosed the pool: **Tesla P100 sm_60 ×3 tickets; torch 2.10+cu128 ships no sm_60 kernels** (fail-fast added, then retired).
- v7 RUNNING: CPU FULL training (measured 1.68 s/iter VM-class → ~3.5 h/20ep; Kaggle CPU similar; inside 12 h cap; per-improvement ckpts retrievable even on timeout). Decision: lottery retired (P100-heavy pool), CPU is the primary path.
- Audit (Stage A parallel, read-only) caught 3 REAL flags pre-completion: (1) HNM slice-overrun crash at ep-1 refresh (verified by reading; FATAL); (2) recall-only ckpt selection ignoring count discipline; (3) MSE-only loss vs design Dice term; plus determinism gaps (cuda seed, sampler offset) and a position/index confusion in HNM boost (second bug, same function). All fixed + locally validated (dice range, HNM unit past old crash class, full --smoke PASS) → pushed v8, RUNNING past old crash point.
- v8 status: ep 3/20, loss 0.5318→0.5018 then flat, val_recall 0.000 (zero-positive start, count-gate withholding best as designed); HNM fired ep1+ep3 (slice fix HOLDS live); ETA ~2.8–3 h. Early warning: recall/cnt still 0 past ep8–10 → threshold/loss review. Logs stream only via `logs -f` while RUNNING.
- Eval ready: `notebooks/train_unet/infer.py` built + unit-tested (5/5 synthetic peaks, 0 decoy FPs) + random-weight dry run green; EXP-0035 run.sh skeleton waits on WEIGHTS_PATH.
- Next: fetch `unet_best.pt` on COMPLETE → EXP-0035 learned-detector evaluation (recall vs GT + edge with trusted scorer v1.1).

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
- `knowledge/`: this file + HYPOTHESES.md (H-001/H-002/H-004/H-005 active; H-003 classical parked, learned-features residual) + RESULTS.md (EXP-0000…0045 rows).
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
- `experiments/EXP-0021/`: DONE 2026-09-10 — image-policy transfer (H-002; reuse verified by position-equality gate): refs hold, but 0b24845f/0c582fdc/05db0fb1 reject (0.325/0.197/0.290); micros 0.341/0.579/worst 0.341. Levels are SAMPLE-specific; per-embryo policy demoted to starting points. Fallback @98.5 suspect on unseen embryos (submit risk).
- `experiments/EXP-0022/`: DONE — half-res DS at window parity (rec/raw/ec IDENTICAL, adj up, 3.8×) → GO EXP-0023.
- `experiments/EXP-0023/`: DONE (Stage A parallel) — full-video DS STOP: 44b6 raw −0.33, 6bba −0.035 (rescore-verified); window parity does NOT generalize. DS parked for quality; NO kernel upgrade.
- `experiments/EXP-0024/`: DONE (Stage A parallel) — pct sweep on 3 dark samples: best rec 0.80/0.50/0.41; fixed percentiles DEAD (bright clutter owns tail; blind cells, not marginal). No wider grids.
- `experiments/EXP-0025/`: DONE (Stage A parallel, read-only) — linking 0.2–0.5% of pipeline everywhere, scaling ~N^1.5 (build-dominated). Bottleneck = DETECTION, not linking.
- `experiments/EXP-0026/`: DONE (Stage C parallel) — ROI-masked DoG STOP: rec 0.77/raw 0.41 vs 0.98/0.95, speedup 1.97× (bar 2×); union ROI covers 99% of dense frames; per-box percentiles diverge both ways. ROI pointless here.
- `experiments/EXP-0027/`: DONE (Stage C parallel, read-only) — internals profile REJECTS gauss-dominance: per-component argwhere loop 58% dense / 85% sparse; label+bincount+pct ~7%/3%. Recommends vectorized centroids (−43%/−79% projected, quality-neutral).
- `experiments/EXP-0028/`: DONE — vectorized centroids ADOPTED (H-005): 0/30 fidelity mismatches, edge parity exact, 1.93× overall (below projections, honestly recorded; split path keeps legacy loop, verified). Detection ~64 s + ~70 s/video; hidden projection improved but tight.
- `experiments/EXP-0029/`: DONE — truncate gate + kernel v6 (H-005): truncate=2.0 REJECTED (20/20 frames differ, rec 0.970, raw 0.9145 — single-frame probes don't transfer; default stays 4.0). Notebook vectorized port verified identical locally; v6 COMPLETE 0.11 h vs 0.36 h (3.3×, same rows) → submitted v6 ref 56147475 (rule held; slots now 0). Hidden projection ~5.5 h.
- `experiments/EXP-0030/`: DONE (Stage A parallel) — min-size {25,50,100} window: raw/ec IDENTICAL 143/2/5; ms25 adj −0.0031 (count cost), ms100 rec −0.006. STOP, min-size stays 50.
- `experiments/EXP-0031/`: DONE (Stage A parallel) — r10 on DETECTED graphs: raw −0.025, div-FP 3 on 0-division window (6 extra edges, 0 possible TP). STOP, image forks parked; oracle r10 standalone stands.
- `experiments/EXP-0032/`: DONE (Stage A parallel, enabling) — 6388 patches 50/50 (471 MB gitignored), verified + deterministic; train_design.md written. GPU path data-ready (dataset published, UNet training RUNNING v8).
- `experiments/EXP-0033/`: DONE (Stage C parallel, analysis) — no GT-free statistic predicts operating level (best rho +0.68 < 0.8). Per-video calibration needs GT or learned estimator.
- `experiments/EXP-0034/`: DONE (Stage C parallel) — per-sample-best transfer 2/3: 0b24845f BREAKS (window 0.80 → full 0.43); others hold. Window selection invalid on small windows.
- `experiments/EXP-0035/`: skeleton (eval-builder): infer.py built+unit-tested, run.sh waits on WEIGHTS_PATH. Awaiting unet_best.pt.
- `experiments/EXP-0036/`: DONE — notebook↔repo drift audit: detect/link/assign/CSV all EQUAL; deltas accepted (gate override, no max-size, no split opts, validator gap). IN-SYNC.
- `experiments/EXP-0037/`: DONE — submit-output rescore (frozen graphs): gate-10-vs-7 churn sole deviation (0113de3b −0.28 adj). Gate is a tunable.
- `experiments/EXP-0038/`: DONE (Stage C parallel) — T-discipline filter STOP: adj −0.0035/−0.0341, TP loss dwarfs FP savings; short tracks carry truth. Park filtering.
- `experiments/EXP-0039/`: DONE (Stage C parallel) — full-video 05db0fb1 @96.0 GO: recall 0.29→0.68, adj 0.209→0.482, T_ratio 0.60; @96 new operating point for this sample (replicate before policy).
- `experiments/EXP-0040/`: DONE (Stage A parallel) — @96 replication MIXED 1/2: 0c582fdc REPLICATES (rec +0.21, adj +0.09), 0b24845f DIVERGES narrowly (rec +0.075 need +0.10, adj +0.083 PASS). No policy change; @96 helps everywhere, bar strict.
- `experiments/EXP-0041/`: DONE (Stage A parallel) — window-best full-video: 0c582fdc HOLDS (0.50→0.49, adj beats @96 bar), 0b24845f BREAKS (0.80→0.49; small-window overstatement again). STOP 1/2, no per-sample policy.
- `experiments/EXP-0042/`: DONE (Stage A parallel, analysis) — higher-moment stats max rho 0.77 < 0.8, LOO 3/6 (nominal 0.81 on 14 tests = luck). STOP; calibration needs learned density estimator.
- `experiments/EXP-0043/`: DONE (Stage A parallel) — full-video 062c8d37 @96.0 DIVERGES (rec 0.867 < 0.90 bar, adj 0.786 < 0.8647; T_ratio 0.89). @96 does not generalize as dense policy. STOP.
- `experiments/EXP-0044/`: DONE (Stage A parallel) — r10 forks on 05db0fb1 image full-video: +2393 proposals buy +7 edge TP at +45 edge FP +35 div FP, 0 div TP. STOP; radius-only proposals fire on clutter. Image forks stay parked.
- `experiments/EXP-0045/`: DONE (Stage A parallel, analysis) — division-evidence audit: 3/4 divisions LOST-AT-DETECTION (7.4–13.4 µm), 1/4 LOST-AT-LINKING (062c8d37 orphan, zero forks emitted anywhere). GO: orphan-driven second-edge pass (EXP-0046) — r10 failed for firing on clutter, not orphans.
- UNet v8: ep3 done, ~1.25 h/epoch observed (NOT ~3.5 h/20ep — timeout risk before ep20, ~20 h ETA vs 12 h cap); val_recall 0.000 flat, count-gate withholding best as designed; HNM fix live. Early-warning checkpoint ep8–10: recall still 0 → threshold/loss review; harvest unet_last.pt on timeout regardless.
- `experiments/EXP-0032/`: DONE (Stage A parallel, enabling) — 6388 patches 50/50 (471 MB gitignored), verified + deterministic; train_design.md written. GPU path data-ready.
- `experiments/EXP-0033/`: DONE (Stage C parallel, analysis) — no GT-free statistic predicts operating level (best rho +0.68 < 0.8; 98.5 spans both regimes → non-monotone). Per-video calibration needs GT or learned density estimator.
- `experiments/EXP-0034/`: DONE (Stage C parallel) — per-sample-best transfer 2/3: 0b24845f BREAKS (window 0.80 → full 0.43; 10-node window vs 51-node truth), others hold. Window selection invalid on small windows; no EXP-0035 policy.
- Submit watch: v6 `56147475` + v1 `56143782`/`803`/`804` all COMPLETE publicScore **0.650** (identical ×4 → end-to-end determinism); v7 gate-7 ref `56153940` SUBMITTED 00:02 UTC PENDING (4 slots left); same-account Forge `56144839` COMPLETE **0.946**. Gap thesis: detection recall (edge level); divisions ≤0.10 secondary; T-penalty amplifier.
- Dark probe (Stage A parallel, /tmp only): 05db0fb1 curve still rises below 97.5 (96.0: rec 0.615 vs 0.41; monotone; T_ratio 0.65; timing flat) but 87% of @96 misses are threshold-blind (median DoG rank 94) — GO for full-video @96.0 test, diminishing returns past ~94. Proposed: EXP-B T-discipline filter (min-track-6 + prune-isolated + frac caps; bar worst-fold +0.02) as next cheap CPU rung.
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
- Next: v7 LB reaction on arrival; UNet weights/timeout → EXP-0035 eval or harvest-or-replan. 4 slots left — spend only on gated winners.

## Next loop steps (cold agent — copy/paste)

```bash
cat knowledge/STATE.md knowledge/HYPOTHESES.md knowledge/RESULTS.md
cat docs/PROTOCOL.md docs/COMPETITION.md docs/AUTH.md PROMPT-GOLD.md
ls experiments/ data/train/
# Auth checks (both WORKS 2026-09-09):
export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"
gh auth status
# Download watch: tail -n 5 /tmp/biohub-subset-dl.log  (expect DONE ok 738 fail 0)
# Loop (EXP-0001…0045 done — read them, don't recreate):
bash scripts/run_loop.sh --dry-run
python3 scripts/score.py --dry-run
python3 scripts/test_score.py
# Next: UNet weights → EXP-0035; @96 replication rung; submit v7 post-reset (see Next above)
```
