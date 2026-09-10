#!/usr/bin/env bash
# Runner for EXP-0025 — Linking-time profile (analysis only, CPU, <20 min).
# Reproduces the per-pair linking profile and writes metrics.json.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 "$ROOT/experiments/EXP-0025/profile_link.py"
echo "[EXP-0025] wrote $ROOT/experiments/EXP-0025/metrics.json"
