# Biohub Cell-Tracking Auto-R&D Repo — 合併深度 Audit 報告
> 合併兩個獨立 audit：
> - **[本 audit]** 9-domain fan-out（agent 跑 repro + 我親自重跑關鍵項）
> - **[外部 report]** 你提供嘅 docx audit（已逐項驗證）
>
> 標記：`✅已確認`（有 repro/code 證據）· `🔄重疊`（兩份 report 獨立發現同一問題）· `💭方法論`（設計意見，非 bug）

## 執行摘要

Ledger 數字本身誠實（484/484 stored score bit-exact 重算通過），**但「trusted」鏈兩端都唔可信**：
1. `score.py` 同官方 scorer 有 **8+ 個實質語義偏差**（雙向 — 有啲高估、有啲低估 vs LB）
2. `trusted_cv.py` 喺原 VM 以外 **完全跑唔到**（hardcode path + 無條件 zarr import），兼且 fold micro 掉咗 +0.1·div term — **EXP-0053 已發佈 `embryo_nested_worst` 應係 0.5193 唔係 0.4193**
3. EXP-0060 `trusted` tag 違反 repo 自己嘅 PROTOCOL §2.3

外部 report 嘅評級判斷（Research process A- / Metric correctness C）同本 audit 結論一致。

---

## 🔴 P0 — Scorer 語義偏差（`scripts/score.py` vs 官方 `tracking_cellmot`）

| # | Finding | 出處 | 驗證 |
|---|---------|------|------|
| S1 | **match_nodes tie-break 錯**：min-sum-distance vs 官方 max-cardinality→max-sum `1/(1+d)`。26k fuzz 有 3.6% scene 配對唔同，可 flip TP↔FP | 本 audit | ✅ 我重跑證實（pairing `{1:3,2:2,3:1}` vs 官方 `{1:3,2:1,3:2}`）|
| S2 | **缺 consecutive-frame filter**：官方計數前丟棄 `t_t - t_s != 1` 嘅 pred edge；repo 照計 FP。實測 t0→t2 edge `{TP:0,FP:1,FN:2}`（官方 FP=0）— **懲罰自己嘅 gap_link** | 🔄重疊 | ✅ 我重跑證實 |
| S3 | **缺 pred-edge dedup + out-degree>2 cap**：duplicate edge double-count TP；>2 outgoing 官方只留 2 條最低 edge-id | 🔄重疊 | ✅ auditor repro |
| S4 | **Division component check 用 unordered set + 只驗 paired 2 branch**：結果隨 node id rename flip；忽略 direct-child precedence + grandchild-ambiguity | 本 audit | ✅ auditor live repro，兩 domain 獨立發現 |
| S5 | **官方 fork 毒化規則缺失**：任何 child branch malformed/cross-component → 官方 reject 成個 fork；repo 只驗 paired 兩條 | 本 audit | ✅ auditor repro |
| S6 | **GT division 用 ≥2 而非官方 ==2**：GT 3-child → repo TP / 官方 FP。實測 3-fork `{TP:1,FP:0,FN:0}` vs 官方 `{TP:0,FP:1,FN:0}` | 本 audit | ✅ 我重跑證實 |
| S7 | **Division FP「considered」類缺失**：anchor-adjacent fork fail topology 官方計 FP；repo 忽略 → division Jaccard 系統性高估 | 本 audit | ✅ auditor repro |
| S8 | **T_true fallback 到 pred-supplied**：`gt.get("T_true", pred.get("T_true"))` — pred 報 len(nodes) 即可 zero 掉 node-count penalty；官方 GT 缺 T_true 直接 exclude | 本 audit | ✅ 我重跑證實（score=1.1）|
| S9 | **Zero-division set 白送 +0.1**：`dden==0 → div_j=1.0`；官方 drop 呢個 term（→ score=edge only）| 🔄重疊 | ✅ 我重跑證實 |
| S10 | **Zero-count sample weight=1**（官方 exclude）；`edge_jaccard(0/0)=1.0`（官方 NaN）；T_true-missing sample 照計 | 本 audit | ✅ auditor repro |
| S11 | **Division window rematch approximation**：repo 用 global match restrict 到 window；官方每個 GT division window 獨立 rematch。code 自己 comment 承認（`score.py:45` "Known approximation"）| 🔄重疊 | ✅ code-read 證實 |
| S12 | **`test_plus1tp_still_tp` assertion 無效**：assert `TP ∈ {0,1}` — 名義上測 ±1tp fork-offset spec，實際乜都唔 enforce（`test_score.py:146`）| 外部 report | ✅ 我 code-read 證實 |
| S13 | Duplicate node ids 同一 t 內 → match map 不一致 | 本 audit | auditor repro |

## 🔴 P0 — Trusted CV harness（`scripts/trusted_cv.py`）

| # | Finding | 出處 | 驗證 |
|---|---------|------|------|
| C1 | **`loso_micro` / embryo fold micro 掉咗 +0.1·div**：`micro_of` 只 weight `r["edge"]`；`loso_worst` 用 composite — min > mean 嘅不可能 envelope。Smoke 實測 loso_micro=0.7239 / canonical=0.8239。**EXP-0053 nested_worst 0.4193 → 應係 0.5193**（fold0 無 division）| 🔄重疊 | ✅ 我重跑 smoke 證實 |
| C2 | **Hardcode `/home/box/workspace/kaggle-biohub-rd`**：canonical trusted runner 喺任何其他機器 crash（FileNotFoundError）— 即使 smoke 需要嘅 artifact 全部 committed | 🔄重疊 | ✅ 我重跑證實 |
| C3 | `ensure_det` line 80 `import zarr` 無條件執行 — manifest 全中都要裝 zarr | 本 audit | ✅ code-read 證實 |
| C4 | HP grid `pct=96` 係 eval-sample probe 之後先加 — search space 本身 eval-informed | 本 audit | auditor git-history |
| C5 | `test_trusted_cv.py` 只測 tie-break；無 leakage / aggregation-equivalence regression | 🔄重疊 | auditor |
| C6 | `fit_best` unused `gt_cache`；`frames=range(100)` hardcode；`loso_table` 掉 T_true/assign provenance | 本 audit | auditor |

## 🟠 Ledger / tag 誠實度（數字啱、tag 唔啱）

| # | Finding | 出處 |
|---|---------|------|
| L1 | **EXP-0060 `cv_tag='trusted'` 違反 §2.3**：rule sign 用 EXP-0059 eval-sample 結果揀 → 最多 `tuned_ref`。呢個係 current best challenger | 本 audit |
| L2 | **EXP-0053 trusted BTE 喺 repo 唔可以 re-derive**：det cache gitignored + 無 pct-97 det + fit table 無存 + runner hardcode | 本 audit |
| L3 | EXP-0059 partial 5/6 LOSO tag trusted，RESULTS drop qualifier | 本 audit |
| L4 | EXP-0018 "promote" cite unperturbed score 做 "worst"（真 min-seed 1.0873 非 1.0884），oracle-based 未 retag | 本 audit |
| L5 | cv_tag 5 個 metrics.json 用 freeform prose（應 5-enum）；protocol_version 三種 stamp 法 | 本 audit |
| L6 | 💭 外部 report 指出 `loso_worst` 作 primary gate 嘅排序可以質疑：train/test 係 embryo-disjoint → `embryo_nested` 先係真 proxy，LOSO 應做 robustness gate | 外部 report |

## 🟠 Pipeline scripts

| # | Finding | 出處 |
|---|---------|------|
| P1 | **`dog_detect.detect()` 喺恰好 1 個 kept component 時 crash**（`center_of_mass` 對 sequence index 已回 list，再行 wrap 變 nested）— 稀疏 frame 必中 | 本 audit |
| P2 | **`gap_link.gap_close()` 實質 no-op**：只有成個 frame 全空先觸發 → EXP-0017「gap pass adds ZERO edges」結論無效；且 GT 全係 dt=1 edge → t→t+2 永遠唔會係 TP | 本 audit |
| P3 | `baseline_link` scipy vs pure-python backend 喺 cost tie 下出唔同 edge set（12/150 crowded case）；`assign` flag 只記最後一次 `_pair` | 本 audit |
| P4 | `graphs_to_csv`：`r10_*` 撞名 last-write-wins；空 dataset 靜靜消失；`--check` 漏 dup node_id | 本 audit |
| P5 | `geff_to_graph` zip-truncate drop nodes；`trusted_cv`/`perturb_graph` strip split/parent keys → phased linking 喺 CV 從未 engage | 本 audit |

## 🟠 Notebooks / submission 鏈

| # | Finding | 出處 |
|---|---------|------|
| N1 | **`submission_skeleton.ipynb` 任何 multi-frame input 都 crash**（`lut` KeyError）— STATE 嘅「15 nodes→12 edges OK」claim 係 false | 本 audit |
| N2 | 同一 skeleton fork proposal 用 stale bookkeeping → 輸出 dt≥2 non-adjacent edge → metric FP + 假 fork | 本 audit |
| N3 | **`train.py` 喺 fold0 holdout embryo 做 ckpt selection** — §2.3 違反 → 出嚟嘅 "trusted" 數字最多 tuned_ref；無 fold1 direction | 本 audit |
| N4 | `submit_gold` `find_test_root` fallback 去最大 .zarr dir（可能係 train tree → dataset id 錯）| 本 audit |
| N5 | instrumentation `peak_thr=0.1` 漏入 ckpt cfg → inference default（EXP-0035 26k-det flood 成因）| 本 audit |
| N6 | `kernel-metadata.json` 仲指住已 cancelled v1 kernel | 本 audit |

## 🟠 Infra / Docs / Competition fidelity

| # | Finding | 出處 |
|---|---------|------|
| I1 | `download_subset.py` 用 kaggle CLI `--format csv`（**PyPI 上唔存在**，只有 unreleased main）+ path scheme 同 main 衝突 + hardcode root + undocumented SUBSET_IDS.txt | 本 audit（verify-agent confirmed）|
| I2 | `run_loop.sh` non-dry exit 0 乜都唔做；`new_experiment.sh` title 有 quote → invalid JSON；EXP-0000 template call 唔存在嘅 `run_loop.py` | 本 audit |
| I3 | **`smoke.yml` 從不 pip install -r requirements.txt、從不跑 trusted_cv --smoke、無 official differential test、無 metrics schema validation** — 所有上述 bug 綠燈直行 | 🔄重疊 |
| I4 | `STATE.md` 頭部 stale「v11 kernel RUNNING，do NOT restart」（2026-09-13，12h cap 下必死）；AUTH.md「gh not logged in」同 STATE「WORKS」同日矛盾 | 🔄重疊 |
| I5 | `.gitignore`「det never commit」vs ~500 det JSON tracked；`requirements.txt` 漏 scipy/zarr/kaggle；deps 無 lock | 🔄重疊 |
| I6 | **Competition docs 漏 merger deadline 2026-09-22 + 5/day cap**；teams count stale 3287→3737；hidden test「~199」claim 只 confirm 咗 train=199 | 本 audit |
| I7 | 全部 kaggle script 假設 username/key `kaggle.json`，但你嘅 auth 係 KGAT Bearer token → 全部會 fail | 本 audit |

## 💭 方法論 / 策略建議（外部 report 為主，本 audit 同意其方向）

1. **Embryo-nested 應做 primary promotion gate，LOSO 做 robustness gate** — Kaggle 講明 train/test embryo-disjoint，LOSO 只驗證同 embryo 新 FOV；embryo_nested 先係 hidden test 嘅真 proxy（不過只得 2 embryos → variance 高，係資料限制）。
2. **6-sample trusted envelope 太細** — train 有 199 movies（71×44b6 + 128×6bba）；EXP-0059/0060 已示範 brightness rule direction、median threshold、per-sample optimum（pct 95→99）全部會 flip。應該用全部 train videos 做 evaluation/HP fitting（weight training 繼續 embryo-disjoint）。
3. **Classical DoG branch 可以畢業** — EXP-0007→0060 已試勻 percentile/watershed/NCC/gap/gate/ROI/threshold/hysteresis，主要問題係 representation capacity。Classical LB 0.668 vs 你自己 Forge learned stack 0.946 vs 榜首 ~0.974；官方 baseline 係 TemporalUNet3D + cross-attention transformer linking（只 train 3 epochs）。Classical 保留做 fallback/sanity/ablation control。
4. **重新考慮 strict causality constraint** — metric 只 constrain **edge** 要 t→t+1，無要求 feature extraction causal；官方 baseline 用 temporal attention。建議改成「禁 future labels/GT，唔禁 future images」（例如 detector 用 t-1,t,t+1 context）。
5. **EXP-0061 success bar 太弱** — 1 sample × 10 frames、無 T_true、「edge>0」唔能夠當 candidate evidence。正確鏈：smoke → heterogeneous windows → full videos → 修好嘅 trusted CV → embryo-disjoint CV → submission dry-run。
6. **CI 升級** — 加 `pip install -r requirements.txt` + `trusted_cv --smoke` + official-scorer differential test + metrics schema validation。

## ✅ Verified-OK（兩份 audit 一致同意冇問題）

- `_hungarian` O(n³) 正確（~10k fuzz 0 suboptimal）；7µm inclusive threshold、voxel 次序、per-t grouping、NaN 處理全啱
- Edge FP two-case rule、adjusted jaccard 公式、a=0.1、micro weighting 同官方一致
- `fit_best` 無 leakage（tripwire-proved）；frozen det artifacts 係 image-only
- Ledger arithmetic：484/484 stored score bit-exact；EXP-0017/18/20 regen 一致；v1.2 主動降格 0.8194→tuned_ref 係正確研究習慣
- 所有 headline pins（voxel、deadline、schema、train=199、video shape）同官方一致
- `fork_link`/`gap_link` 保持 temporal causality；`appearance.label_edges` 忠實 mirror `edge_counts`
- train.py 5 個 claimed fix（HNM、count gate、weighted-MSE、CUDA seeding、position/index）全部已修

## 建議修復優先序

1. **S 系列 — `score.py` 對齊官方**（最影響所有 trusted 數字；S1/S2/S5/S6 改 score direction，S3/S8/S9/S10 改 magnitude）
2. **C 系列 — `trusted_cv.py`**（micro 補 +0.1·div、path repo-relative、zarr lazy import；重標 EXP-0053 standing 0.5193）
3. **L 系列 — tag 誠實度**（EXP-0060→tuned_ref；commit per-cell score tables）
4. **N1/N2 — `submission_skeleton`**（submission 源頭 crash + corrupt）
5. **P1/P2 — `dog_detect` crash + `gap_link` no-op**
6. **I 系列 — infra/docs**（download_subset、kaggle auth、CI、STATE hygiene）
7. 方法論項：gate 排序、6-sample 擴充、causality 放寬 — 屬於 direction 決定，改 protocol 前先傾

> ⏰ **Merger/new-entrant deadline 2026-09-22（~2 日後）**；最終 deadline 2026-09-29。
