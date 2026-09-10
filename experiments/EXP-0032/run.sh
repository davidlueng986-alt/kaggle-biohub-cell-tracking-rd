#!/usr/bin/env bash
# Runner for EXP-0032 — Training patch export (CPU-only, no training).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0032"
T0=$SECONDS
echo "[EXP-0032] exporting patches..."
python3 "$EXP/export_patches.py" --out "$ROOT/data/patches" --seed 0
echo "[EXP-0032] verifying + writing metrics.json..."
python3 "$EXP/verify_patches.py"
echo "[EXP-0032] done in $((SECONDS - T0))s"
