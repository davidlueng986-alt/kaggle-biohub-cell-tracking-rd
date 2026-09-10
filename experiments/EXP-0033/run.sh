#!/usr/bin/env bash
# Runner for EXP-0033 — Calibration-statistic mapping (ANALYSIS ONLY).
# Computes GT-free per-video stats on window t20-29 for the 6 subset samples,
# rank-tests each stat vs assembled best-pct + LOO notch error, writes
# metrics.json with the GO/STOP verdict. CPU-only, deterministic.
# Fresh compute: 60 DoG frames + 100 probe threshold/labels (<=120 cap);
# 20 @99.0 probe counts reused from EXP-0008 with thr-equality gate.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0033] calibrating 6 samples x t=20..29 (~1 min CPU)..."
python3 "$EXP_DIR/calibrate.py"
echo "[EXP-0033] OK: metrics.json written."
python3 -c "import json;m=json.load(open('$EXP_DIR/metrics.json'));print('[EXP-0033] verdict=%s best=%s' % (m['verdict'], m['best_stat']))"
