# STATE — cold resume in ≤5 min

Last updated: 2026-09-12 (frontier BLOCKED ×11; ledger clean; LB steady, slots 5). Maintainer: gold-watch.
Prior: scorer v1.1 + EXP-0002 green. `PROMPT-RD-SYSTEM.md` done; active brief is `PROMPT-GOLD.md` (continuous gold run, PM owns go).

## Reporting policy (PM 2026-09-12)
- To Alex: **try get higher mark** — no「打贏基準／BTE」talk. Always include concrete trusted CV numbers + LB.
- Public diagnostic reference: **0.668** (v7 gate-7). Forge 0.946 still untrusted.
- Trusted CV stays for honesty / anti-leakage; not an oral BTE ritual.

## OpenCode execution standard (PM 2026-09-12)
- AI Master MUST open OpenCode **web UI** at `http://127.0.0.1:5096/` session `ses_f79cedb0fffepcQrAHaF52L2cf` (not curl-only).
- Session agent mode MUST be **`orchestrator`** with Stage A **multi-agent parallel** (`@general` fan-out). Never nudge with `agent: build` as the primary mode.
- Blind `prompt_async` with `agent: build` is a process failure.

## EXECUTION OWNER (PM handoff 2026-09-11 ~20:28 HKT)
- **AI Master** owns the continuous gold R&D **execution** loop (OpenCode nudge, EXP runs, UNet harvest, ledger updates, working-status to Alex).
- **PM** remains sole product authority (goals, PROTOCOL, BTE policy, acceptance). Contact PM for policy / out-of-brief / final done-failure.
- Handoff brief delivered to AI Master with full trusted-CV + session context (no context loss intended).

## PRIORITY (PM 2026-09-11)
- **Trusted CV rebuild ACTIVE (PROTOCOL v1.2).** Standing image 0.8194 is `tuned_ref` only — not trusted.
- BTE = EXP-0053 trusted `loso_worst` **0.2092** / `embryo_nested_worst` **0.4193** (fold0 0.4193 / fold1 0.6136). Challengers must beat this envelope. **Do not BTE Forge 0.946** (`lb_external_untrusted`).
- Spec: `docs/TRUSTED_CV.md` + `docs/PROTOCOL.md` §2. Ledger: `knowledge/LB_CALIBRATION.md`.

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

- **FROZEN v1.2**: `docs/PROTOCOL.md` (faithful scorer v1.1.0: per-timepoint 7 µm Hungarian, pinned voxel, T_true=`estimated_number_of_nodes`, division window, submission.csv micro-average; embryo folds fold0 holdout `44b6` / fold1 holdout `6bba`; causality rule; 5 promotion gates; worst-fold ensemble; leakage checklist; compute budget).
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
- Next: UNet v10 harvested + EXP-0035 REJECT (done); LB reaction on movement; v11 needs PM/train-owner green-light; frontier BLOCKED ×10 (no manufactured rungs).

## Auth status (verification commands — re-run, do not assume)

- Kaggle CLI (`~/.local/bin/kaggle`): **WORKS (verified 2026-09-09 by repo-hardener: `kaggle competitions list --search "biohub"` exit 0, returned `biohub-cell-tracking-during-development`, userHasEntered=True)**:
  `export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"`
  then `kaggle competitions download -c biohub-cell-tracking-during-development -p data/` (requires Rules acceptance on competition page first).
- `gh`: **WORKS (verified 2026-09-09: logged in as davidlueng986-alt, remote HEAD in sync)**. Repo: https://github.com/davidlueng986-alt/kaggle-biohub-cell-tracking-rd (exists). Push frequent small commits.
- Subset download DONE 2026-09-09 (PROMPT-GOLD §1, after early-stop fix): 6 ids (3×44b6 + 3×6bba, embryo-paired), 738/738 files ok 0 fail, 2.6 GB in `data/` (gitignored). EDA needs `pip install zarr numcodecs` — DONE (zarr 3.3.0 on VM).
- Never commit secrets. See `docs/AUTH.md`.
- Never commit secrets. See `docs/AUTH.md`.

## What exists

- `docs/`: PROTOCOL.md (FROZEN v1.2), COMPETITION.md (submission schema + voxel + T_true verified 2026-09-09), AUTH.md, TRUSTED_CV.md (operational brief).
- `scripts/`: score.py v1.1.0 (faithful), test_score.py (13 tests, all pass), trusted_cv.py (v1.2 LOSO + embryo-nested harness), run_loop.sh, new_experiment.sh. `requirements.txt` (numpy>=2.0).
- `experiments/EXP-0000/`: template; `run_loop.sh --dry-run` validates it.
- `experiments/EXP-0001/`: DONE — legacy toy harness re-scored under v1.1 (fold0 0.5/1.0/0.6 hand-calc match, `dry_run:true`, keep-trying). Do not recreate.
- `experiments/EXP-0002/`: DONE 2026-09-09 — full-scorer geometric validation (H-001+H-004): perfect 1.1 / idswitch 0.333 (FP≥1) / inflated adj 0.9 / division TP then FN; 6/6 checks pass; `dry_run:true`, keep-trying (no real data, NOT promotable).
- `experiments/EXP-0003/`: DONE 2026-09-09 — FIRST REAL-DATA result (H-001+H-002): oracle GT nodes + causal Hungarian linker on subset 6 → 44b6-micro 1.0933 / 6bba-micro 1.0705 / worst 1.0705; div 0/0/4 (no forks); `real_data:true`, keep-trying (floor, not a model). Helpers: `scripts/geff_to_graph.py`, `scripts/baseline_link.py`.
- `experiments/EXP-0004/`: DONE 2026-09-09 — fork-proposing variant (H-002+H-003, `scripts/fork_link.py --propose-um 15.0`): fold0 44b6 unchanged (+0.0000), fold1 6bba micro −0.0025, div sums 0/0/4→3/10/1. Sub-gate REJECT for promotion (edge regression on fold1; single-seed cap anyway). Signal kept: 3/4 GT divisions geometrically recoverable → EXP-0005 tighter gating.
- `experiments/EXP-0005/`: DONE 2026-09-09 — radius ablation {9,10,11,12}+isolation: r9 +0.0004 div 1/0/3; **r10 SELECTED** (+0.0011 fold1, div 3/0/1, FP=0, plateau r10==r11); r12 +0.0008 div 3/1/1; r15+iso −0.0011 div 4/7/0. fold0 identical grid-wide. Sub-gate numeric PASS; keep-trying (no fold0 win possible + single-run ceiling). r10 = ensemble-candidate.
- Submit path (GOLD §5, skeleton): `scripts/graphs_to_csv.py` (writer + `--check`; demo 4 subset preds → valid 4294-row CSV) + `notebooks/submission_skeleton.ipynb` (5 cells compile; demo wiring 15 nodes→12 edges OK) + `notebooks/README.md`. DRAFT — no submit yet; detector+weights TODO.
- `knowledge/`: this file + HYPOTHESES.md (H-001/H-002/H-004/H-005 active; H-003 classical parked, learned-features residual) + RESULTS.md (EXP-0000…0060 rows).
- `experiments/EXP-0006/`: DONE 2026-09-09 — r10 replication (H-002+H-003, `scripts/perturb_graph.py` σ=0.3vox × seeds {0,1,2} + noise-matched base arm + corrected same-set LOO): literal-identical FAIL (seed0 div 2/0/2; ±0.005 wobble is base-linker's, shared by both arms); refined PASS (variant≥base 18/18, FP=0 all seeds, LOO 6/6). r10 KEEPS ensemble-candidate; boundary-pair fragility → H-003 appearance case.
- `experiments/EXP-0007/`: DONE 2026-09-09 — DoG detection probe (H-002, `scripts/dog_detect.py`, CPU ~1s/frame): pct99 recall 1.00 both samples; 6bba mini-graph edge_raw 0.8462 (first meaningful image-based number); over video budget unoptimized (H-005 flag).
- `experiments/EXP-0008/`: DONE 2026-09-09 — full-frame sweep (H-002+H-005): 44b6 recall 1.000 edge_raw 0.9038 (strong); 6bba recall 0.835 (FALSIFIED <0.90 → pct99 dead for dense tissue; fix = level @98.5, threshold already per-frame). Curve monotone. Timing 2.05/0.84 s/frame (H-005 debt quantified). Infra: scipy fast path (floor bit-identical).
- `experiments/EXP-0009/`: DONE 2026-09-09 — full-video @98.5 (H-002): 44b6 adj −0.010 (raw identical — pure count cost) vs 6bba adj +0.107 (raw 0.7989, recall 0.893). Level SPLITS by sample → per-embryo levels (44b6@99.0 + 6bba@98.5) next; T_ratio 0.73–0.74 (bonus holds, crossover watched).
- `experiments/EXP-0010/`: DONE 2026-09-09 — combo + window probe (H-002): combo adj 0.9382/0.8194, worst 0.8194 ≥ both uniforms (all 4 combo checks pass); 6bba@98.0 window recall 1.000 det/f 57 → EXP-0011 full-video @98.0 GO. [RETAG v1.2: `tuned_ref` — levels chosen on scored samples; superseded as standing by trusted rebaseline.]
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
- `experiments/EXP-0035/`: DONE (Stage A parallel) — FIRST LEARNED EVAL, unet_best.pt ep4 harvested (gated pre-divergence; earlier "never saved" watch claims corrected — cnt==1.00 passes the gate with recall 0): learned recall 0.988 (83/84) at 26k det/frame → raw/adj 0.0. REJECT all gates. Count explosion is the disease; v11 = calibration/threshold + gated training past ep4.
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
- `experiments/EXP-0047/`: DONE (Stage A parallel, linking-only) — gate-10 vs gate-7 on dark+ref: HOLD-g7 3/5 (0b24845f −0.002, 05db0fb1 −0.017, 05b6850b −0.006; g10 wins 0c582fdc +0.026, 062c8d37 +0.013). Gate sample-conditional; v7 gate-7 safe default. Overlaps concurrent EXP-0050 — cross-check, no rerun.
- `experiments/EXP-0048/`: DONE (Stage A parallel, enabling) — harvest drill READY: random-weight infer live (25.7k nodes/3f, 227s; thr-0.3 garbage expected), link skipped OOM-by-design; unet_best.pt → EXP-0035.
- `experiments/EXP-0049/`: DONE (this session) — notebook↔repo drift re-audit on current submit_gold: detect 6/6 + link 2/2 + statics 5/5 EQUAL. IN-SYNC; accepted deltas stand.
- `experiments/EXP-0050/`: DONE (this session, Stage A parallel) — gate-7-vs-10 all-6 image graphs: gate-7 wins 4/6 (0113de3b +0.28); gate-10 flips 0c582fdc (+0.026) + 062c8d37 (+0.013) where TP gain beats FP cost. MIXED: no global flip; agrees with EXP-0047 (same 2 flips) — independent cross-validation.
- `experiments/EXP-0051/`: DONE (Stage A parallel, analysis) — gate-regime interaction: fast-frac rho −0.38 image (flips idiosyncratic) vs +1.00 oracle. WEAK: keep uniform gate-7.
- `experiments/EXP-0046/`: DONE (single agent) — orphan pass STOP: true site recovered but buried (div-FP 18; control fires 3904 forks; edge regresses both). Orphan-ness not selective in dense fields; parked with r10. Division needs beyond-proximity signal (learned/GPU).
- UNet v8: ep3 done, ~1.25 h/epoch observed (NOT ~3.5 h/20ep — timeout risk before ep20, ~20 h ETA vs 12 h cap); val_recall 0.000 flat, count-gate withholding best as designed; HNM fix live. Early-warning checkpoint ep8–10: recall still 0 → threshold/loss review; harvest unet_last.pt on timeout regardless.
- UNet v9 TRIAGE-DRIVEN (Stage A parallel): loss == all-zero baseline (0.5018) + 159fg/36705bg + neg-Dice veto = zero-collapse attractor (not slow learning). Fix bundled: HNM off + foreground-weighted MSE ×200 (attribution via trajectory; embryo discipline preserved). Validated locally (smoke + 1 real epoch, no crash). Pushed v9, RUNNING (no instant-fail). Watch: loss < 0.50 early = escaped.
- UNet v10 TRIAGE-DRIVEN-2 (Stage A parallel triage: ep8, loss bit-frozen 0.7065, zero grads at sigmoid=0.0f, breakeven ≈1350): HNM off kept + fg-weight ×2500 + Dice OFF + thr 0.1 + lr 1e-3. Local 60-iter probe: iter-0 loss 0.4268 (predicted 0.4–0.6 ✓), moving. Pushed v10, RUNNING. Watch: ep0 loss ≠ 0.7065/0.8574 + recall > 0 by ep2–3.
- UNet v9 ESCAPED then FLAT (watch 2026-09-11 17:21 HKT): ep0 loss 0.8574 → ep1–7+ loss 0.7065 flat; val_recall=0.000 cnt=0.00 all epochs; HNM silent (off); still RUNNING past early-warning. Action: OpenCode nudged for threshold/loss review + Stage A parallel; harvest unet_last.pt on COMPLETE/timeout → EXP-0035 regardless.
- `experiments/EXP-0052/`: DONE (Stage A parallel) — hidden-timing calibration: det fit R²=0.995 (Kaggle-anchored R²=0.993); projections sparse 5.80 h / mix 6.04 h / dense-worst 6.30 h (≥1.9× headroom); v7 visible 0.1214 h re-confirmed; hidden logs unrecoverable (boundary recorded). Timeout fear RETIRED quantitatively.
- `experiments/EXP-0053/`: **DONE** 2026-09-11 — trusted CV rebaseline (H-002+H-004, v1.2): loso_micro 0.4826 / loso_worst **0.2092** (05db0fb1) / embryo_nested_worst **0.4193** (fold0 44b6 0.4193 / fold1 6bba 0.6136); HPs vary per holdout (pct 96–98.5, gate 7); confirms selection-leakage vs tuned_ref 0.8194; decision keep-trying (defines BTE, not a promotion).
- `experiments/EXP-0054/`: DONE (Stage A parallel, analysis) — GT-free count-target analysis over 13 frozen rows: pooled bins rise only via embryo confound; within-sample optima diverge (05b6850b peaks T≈0.74, 062c8d37 T≈0.84); T_ratio needs GT T_true → circular as GT-free rule. Verdict NOT_EXISTS.
- `experiments/EXP-0055/`: DONE (Stage A parallel) — full-video 05db0fb1 @95.5: recall 0.7135 / adj 0.5159, beats @96.0 bars (+0.038/+0.034); T_ratio 0.62; div 0. Descent hasn't turned; next rung @95.0.
- `experiments/EXP-0056/`: DONE (Stage A parallel) — full-video 05db0fb1 @95.0: recall 0.750 / adj 0.547, beats @95.5 (+0.037/+0.031); T_ratio ~0.64; div 0. Descent STILL hasn't turned; next rung @94.5.
- `experiments/EXP-0057/`: DONE (Stage A parallel) — full-video 05db0fb1 @94.5: recall +0.014 BUT adj −0.0069 (TP +1 vs FP +18). Descent TURNED: merging/displacement dominates below 95.0. @95.0 (0.750/0.547) LOCKED as operating point; do not descend without linker-side merge handling.
- `experiments/EXP-0058/`: DONE (Stage A parallel) — threshold-hysteresis union (@99∪@95/3µm) on 05db0fb1 window: +1 GT node for +829 detections (cost 829/match vs ≤10 bar). STOP; halo is clutter. Single-threshold @95.0 stands.
- `experiments/EXP-0059/`: DONE (Stage A parallel) — nested binary-brightness rule: split perfect, sign INVERTED (known-dark samples have highest means 627–1009 vs 62–256: bright clutter dominates). loso_worst 0.161 / micro-edge 0.433 / nested 0.342 — all below BTE. Follow-up specified: sign-corrected HIGH-B→96 (needs 062c8d37@99, 100 frames).
- `experiments/EXP-0060/`: DONE (Stage A parallel) — sign-corrected HIGH-B→96: loso_worst 0.2872 ✓ / micro 0.6272 ✓ / nested_worst 0.3631 ✗ (fit-6bba 3-sample median forces all-44b6 onto @96, count-costing bright 0113). 2/3 bars: binary rules EXHAUSTED both signs (small-sample medians flip). No per-regime policy.
- UNet v10 ep7 (watch): DIVERGENCE deepening (loss →2.54, recall 0 ×4, cnt collapsed to 0.01); best never saved; timeout-harvest (unet_last.pt, likely collapsed) expected. v11 needs train-owner lr/loss-scale review — PROPOSED, not pushed (PM direction required).
- UNet v10: ep0 confirmed again (loss 0.1763, recall 0.925 over-detected, gate withholding); pace suggests timeout before ep20 → harvest unet_last.pt path stands; count-gate must see cnt fall into [0.7,1.0] with recall held.
- UNet v10: ep0 confirmed (loss 0.1763, recall 0.925 over-detected, gate withholding best); CPU pace ~1.25 h/epoch → 20ep exceeds 12 h cap → plan TIMEOUT-harvest (unet_last.pt), not clean COMPLETE.
- UNet v10 ep1 (watch): loss 0.1763→0.1369 FALLING, recall 0.839 held high, cnt 1.84 still over-dense (gate withholding correctly); no crash. Training HEALTHY — remaining gap is precision/count discipline, not escape. Timeout-harvest stands (many hours out).
- UNet v10 ep2 (watch): loss 0.1338 falling, recall 0.914 held, cnt 1.91 stuck over-dense (gate withholding all 3 epochs). Precision gap persists; timeout-harvest (unet_last.pt) expected, not clean COMPLETE.
- UNet v10 ep3 (watch): loss 0.1432 UPTICK (0.1338→0.1432), recall 0.937 held, cnt 1.94 stuck (gate withholding all 4). First loss reversal — watch for flat/divergence next epochs; timeout-harvest stands.
- UNet v10 ep4 (watch): INSTABILITY EVENT — loss SPIKE 0.1432→0.4420, recall 0.937→0.000 (detections exist cnt 1.00 but match nothing), fpr 1.000. lr 1e-3 × fg×2500 suspected (not gradual drift). ep5 is the tell: rebound → keep watching; still 0/diverged → escalate to train-owner (lr/loss-scale review, runbook §g kill triggers). No weights; harvest on timeout/COMPLETE only.
- UNet v10 ep4 re-confirmed (watch): fpr=1.000 ALL epochs (fires everywhere — count-explosion risk); best-SAVE STATUS SUPERSEDED (see HARVESTED line: ep4 saved gated-vacuous); ep5 still computing (slow epoch). Timeout-harvest likely; count-gate may yield NO USEFUL gated best.
- UNet v10 ep9 (watch): diverged plateau persists (loss 2.57 flat, recall 0 ×6, cnt ~0.03); AT THE TIME best appeared unsaved — SUPERSEDED by harvest (ep4 gated-vacuous best exists). Frontier re-audit BLOCKED again (ensemble probe non-promotable by construction: oracle tag, gates 1+3 fail).
- UNet HARVESTED (timeout at ep9, ~43k sec = 12 h cap hit): data/weights/unet_best.pt (ep4 gated-vacuous recall-0) + unet_v10_timeout_last.pt (ep9 diverged) — both gitignored, loadable (keys model/cfg/ep). Last-eval SKIPPED deliberately (training recall 0 ⇒ expected zero; CPU better spent). v11 needs PM/train-owner green-light.
- UNet v10 ep8 (watch): divergence PERSISTS (loss →2.57, recall 0 ×5, cnt ~0.01); AT THE TIME best appeared unsaved — SUPERSEDED by harvest (ep4 gated-vacuous best exists). No weights then; timeout-harvest (unet_last.pt, collapsed) expected. v11 review with train-owner/PM (lr/loss-scale) — proposed, not pushed.
- UNet v10 ESCAPED (watch): ep0 loss 0.1763 (≠ 0.7065), recall 0.925 via over-detection (fpr 1.0, cnt 1.93 — gate correctly withholding best). Fix works mechanically; count discipline is now the training target.
- `experiments/EXP-0032/`: DONE (Stage A parallel, enabling) — 6388 patches 50/50 (471 MB gitignored), verified + deterministic; train_design.md written. GPU path data-ready.
- `experiments/EXP-0033/`: DONE (Stage C parallel, analysis) — no GT-free statistic predicts operating level (best rho +0.68 < 0.8; 98.5 spans both regimes → non-monotone). Per-video calibration needs GT or learned density estimator.
- `experiments/EXP-0034/`: DONE (Stage C parallel) — per-sample-best transfer 2/3: 0b24845f BREAKS (window 0.80 → full 0.43; 10-node window vs 51-node truth), others hold. Window selection invalid on small windows; no EXP-0035 policy.
- Submit watch: v6 `56147475` + v1 `56143782`/`803`/`804` all COMPLETE publicScore **0.650** (identical ×4 → end-to-end determinism); v7 gate-7 ref `56153940` COMPLETE publicScore **0.668** (+0.018 — gate verdict transfers to hidden embryos); Forge `56144839` COMPLETE **0.946**. Gap thesis holds: detection recall (edge level); divisions ≤0.10 secondary.
- Dark probe (Stage A parallel, /tmp only): 05db0fb1 curve still rises below 97.5 (96.0: rec 0.615 vs 0.41; monotone; T_ratio 0.65; timing flat) but 87% of @96 misses are threshold-blind (median DoG rank 94) — GO for full-video @96.0 test, diminishing returns past ~94. Proposed: EXP-B T-discipline filter (min-track-6 + prune-isolated + frac caps; bar worst-fold +0.02) as next cheap CPU rung.
- `opencode-web.png`: local screenshot, git-ignored (not deleted).
- Subset download DONE 2026-09-09 (738/738, 2.6 GB in `data/`, gitignored). EDA deps installed (zarr 3.3.0 + numcodecs, CPU-only).

## Current best — PROMOTED 2026-09-09 (EXP-0018, pre-registered bar)

- **Gate-10 oracle links: worst-fold edge 1.0884** (44b6 1.0998 / 6bba 1.0884), div 0/0/4, FP+1 vs old floor. Replicated: all 3 jitter seeds ≥ floor both folds + ≥ matched base, div-neutral identical, FP==1, LOO clean. Wider gate MORE robust under noise.
- EXP-0019 CANDIDATE: gate-10+r10 combo, worst-fold 1.0895, div 3/0/1, fold0 identical (0 clean-tissue forks).
- EXP-0020 verdict: promotion DENIED (seed0 −4e-4), candidacy REVOKED per pre-registered rule — narrowly, as designed. Config retained in variant pool; re-nomination path = appearance-confirmed forks (jitter-invariant evidence).
- Superseded floor: EXP-0003 gate-7 (worst 1.0705) — kept for reference, no longer the number to beat.
- Standing IMAGE policy (submittable path): submit still uses 44b6@99.0 + 6bba@98.5 gate-7 (LB 0.668); tuned_ref worst adj 0.8194 is NOT BTE. **Trusted BTE = EXP-0053** loso_worst 0.2092 / nested_worst 0.4193 — image side rejected widening; oracle best is not submittable (needs GT nodes).
- r10: ensemble-candidate, re-scoped onto the new best (proposals validated on gate-7 links; combination untested).
- Harness (toy): EXP-0001 0.600/0.333; EXP-0002 perfect 1.1, idswitch 0.333.
- Next: v11 calibration/threshold direction needs PM/train-owner green-light (not pushed); LB reaction on movement; 4 slots left. Harvested weights: data/weights/unet_best.pt (gitignored, ep4).

## Next loop steps (cold agent — copy/paste)

```bash
cat knowledge/STATE.md knowledge/HYPOTHESES.md knowledge/RESULTS.md
cat docs/PROTOCOL.md docs/COMPETITION.md docs/AUTH.md PROMPT-GOLD.md
ls experiments/ data/train/
# Auth checks (both WORKS 2026-09-09):
export PATH="$HOME/.local/bin:$PATH" && kaggle competitions list --search "biohub"
gh auth status
# Download watch: tail -n 5 /tmp/biohub-subset-dl.log  (expect DONE ok 738 fail 0)
# Loop (EXP-0001…0052 + 0053/BTE + 0054/0055/0056/0057/0058/0059/0060 done — read them, don't recreate):
bash scripts/run_loop.sh --dry-run
python3 scripts/score.py --dry-run
python3 scripts/test_score.py
# Next: LB watch / UNet timeout-harvest already complete; v11 needs PM direction; frontier BLOCKED ×10 (see Next above)
```
