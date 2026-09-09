# Notes — EXP-0011 Full-video 6bba@98.0 (H-002)

## Log
- 2026-09-09: `bash experiments/EXP-0011/run.sh` → exit 0, double
  falsification recorded (recall 0.880 < 0.95; adj 0.8063 < 0.8194).
- Numbers: 4910 detections (49/frame — only +4% vs @98.5's ~47) → 4346
  links [pure]; ec 685/24/160 vs @98.5's 699/30/146 (fewer TP AND fewer
  FP, more FN); T_ratio 0.77 (still bonus, crossover not reached).
- Mechanism (diagnosed, not guessed): LOWER threshold in dense 6bba tissue
  MERGES neighboring cells into big components — centroids displace past
  the 7 µm gate (recall falls despite more raw detections) and merged blobs
  link worse (TPs fall). det/f barely rising (+4%) while threshold dropped
  is the smoking gun for merge-dominated regime. Window t0–9 @98.0 hit
  1.00 because early frames are sparser — window gates do not transfer
  across density regimes (lesson for future probes: gate windows must span
  density variation).
- Descent STOPS here per the written stop rule: 6bba level locks @98.5
  (recall 0.893, adj 0.8194). Further gains need SPLITTING merged blobs
  (watershed/size-decomposition on components) or scale/appearance terms —
  not lower thresholds.

## Decisions
- `keep-trying` — standing image-based policy confirmed: 44b6@99.0 +
  6bba@98.5 (combo worst 0.8194). Oracle floor (1.0705) still the reference.
- Next: EXP-0012 watershed/splitter on oversize components (H-002) targeted
  at 6bba dense frames; success = recall up with det/f controlled and adj
  above 0.8194.
