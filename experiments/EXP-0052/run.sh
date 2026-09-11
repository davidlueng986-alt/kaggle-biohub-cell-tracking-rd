#!/usr/bin/env bash
# Runner for EXP-0052 — H-005 hidden timing calibration (READ-ONLY analysis).
# 1. Fetch the v7 kernel log (visible COMPLETE run) via Kaggle CLI (logs only).
# 2. Parse per-video timing table + calibrate local det model + project hidden.
# 3. Emit metrics.json. CPU-only, deterministic, no uploads/pushes/submits.
set -euo pipefail
EXP="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP/../.." && pwd)"
LOG="$EXP/v7_visible.log"
echo "[EXP-0052] fetching v7 kernel log (read-only)..."
~/.local/bin/kaggle kernels logs liangwanyiudavid/biohub-gold-v1-dog-per-embryo-gate-10 > "$LOG"
echo "[EXP-0052] calibrating + projecting..."
python3 "$EXP/calibrate.py" --log "$LOG" --root "$ROOT" --out "$EXP/metrics.json"
echo "[EXP-0052] done: $EXP/metrics.json"
