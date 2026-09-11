# Notes — EXP-0054 GT-free count target analysis (T_ratio vs edge)

## Log

- Scaffolded via scripts/new_experiment.sh (EXP-0054 confirmed free).
- All 10 frozen metrics.json present (EXP-0044 present, used).
- run.sh executed green: 13 unique rows, asserts passed (harvest == frozen).

## Decisions

- VERDICT: NOT_EXISTS — no GT-free count target beats per-sample tuning.
- Pooled bins rise monotonically (0.129 / 0.603 / 0.779; 1.0+ empty) ONLY
  because of the embryo confound (only bright samples reach high T); the
  inverted-U lives within-sample: 05b6850b peaks at T≈0.74 (splitter arm
  T≈0.99 costs −0.091 raw via FP 30→168, not T-penalty), 062c8d37 peaks at
  T≈0.84 (@96 T≈0.89 costs −0.073), 0113de3b flat 0.9038 over T 0.62–0.73.
- Dark samples monotonic-rising over observed range (05db0fb1 +0.267 to
  T=0.60; 0b24845f +0.084 to T=0.70; 0c582fdc +0.089 to T=0.56) — peaks
  uncaptured, so even the best-T span [0.56, 0.84] understates spread.
- Killer facts: best-det/f spans 47–420 (9×); pooled det/f Spearman −0.25 <
  T_ratio +0.59; within-sample det/f ≡ T_ratio up to per-sample scale, so
  det/f adds nothing; T_ratio needs GT T_true → circular as a GT-free rule.
- EXP-0044 mechanism note: fork arm at identical counts changes raw by only
  −0.0014 while adding 35 div FPs — count discipline dominates linker tweaks.

## Next-stage input (for RESULTS/STATE)

- EXP-0054 DONE, verdict NOT_EXISTS. Bins: [0–0.5] n=3 mean_raw 0.129;
  [0.5–0.8] n=7 mean 0.603; [0.8–1.0] n=3 mean 0.779; [1.0+] n=0.
  Spearman T_ratio–raw +0.594, det/f–raw −0.250 (n=13).
  Best-T span [0.56, 0.84] (3/6 censored-rising); best-det/f span [47, 420].
- Hidden-test operating discipline stays an OPEN problem; do not promote any
  fixed detections/video prior. Embryo caveat: 2 train embryos only, hidden
  embryo-disjoint; per-embryo tuning itself suspect on unseen embryos.
