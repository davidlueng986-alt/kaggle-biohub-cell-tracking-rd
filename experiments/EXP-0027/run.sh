#!/usr/bin/env bash
# Runner for EXP-0027 — Detection-internals profile (analysis only, CPU, <15 min).
# Times each stage inside DD.detect() on 10 frames (2 videos x t=20..24)
# and writes metrics.json. scripts/dog_detect.py is imported read-only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 "$ROOT/experiments/EXP-0027/profile_detect.py" --out "$ROOT/experiments/EXP-0027/metrics.json"
echo "[EXP-0027] wrote $ROOT/experiments/EXP-0027/metrics.json"
