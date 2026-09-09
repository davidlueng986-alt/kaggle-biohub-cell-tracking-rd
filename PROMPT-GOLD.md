# PM brief — Biohub Cell Tracking: AIM GOLD (continuous)

Owner: PM. Executor: OpenCode (Muse Spark 1.3 contributor, xhigh, Orchestrator). Repo: https://github.com/davidlueng986-alt/kaggle-biohub-cell-tracking-rd

## North star
Maximize **private-LB durable** score for `biohub-cell-tracking-during-development`. Public LB is diagnostic only. Target: **gold-zone** competitive score under PROTOCOL v1.1 (embryo-grouped CV, trusted scorer, anti-shakeup gates). Deadline: **2026-09-29 23:59 UTC**.

## Constraints (hard)
- VM: **no GPU**, ~108GB free. Do **NOT** download full ~88GB. Pull a **subset**: ≥2 samples from embryo `6bba` and ≥2 from `44b6` (full `.zarr` + `.geff` for those sample ids), plus `sample_submission.csv` (already present).
- Full training / 12h notebook inference: **Kaggle notebooks** (GPU, no internet). Bundle weights; no secret commits.
- Always-allow already configured. Push frequent small commits to GitHub.
- Never optimize for public LB alone. Promotion only via PROTOCOL gates.

## Workstream order
1. **Data subset**: scripted download of chosen sample ids into `data/` (gitignored). Document ids in `knowledge/STATE.md`.
2. **EDA + leakage check**: confirm embryo_id grouping, sparse GT, voxel scale, T_true; update COMPETITION.md only if facts change.
3. **Baseline EXP-0003**: real-data unsupervised / tracking baseline on subset; write metrics with trusted scorer; decision keep-trying or promote.
4. **Model ladder toward gold** (parallelizable hypotheses): detection→link; division-aware linking with PROTOCOL division sub-gate; shake-up ensemble (worst-fold); latency budget ≤80–96s/video on T4-class.
5. **Kaggle notebook path**: submission notebook that loads bundled weights, runs offline ≤12h, emits valid `submission.csv`.
6. **Submit** when gates pass; record LB diagnostic + local score; iterate.

## Acceptance (PM)
- Continuous R&D loop running with STATE/HYPOTHESES/RESULTS updated each experiment.
- At least one **real-data** experiment (not toy) scored by `scripts/score.py` v1.1.
- Kaggle notebook skeleton + run instructions ready; first serious submit attempted when local gates allow.
- Repo pushed; cold agent can resume from STATE.md in ≤5 min.
- Report blockers (disk/GPU quota/API) immediately to PM chat.

Start now: load kaggle skill, select subset sample ids, download, then EXP-0003 plan→run. Orchestrator may skip Phase-2 user confirm — **Alex authorized continuous gold run; PM owns go**.
