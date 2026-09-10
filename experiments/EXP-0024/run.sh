#!/usr/bin/env bash
# Runner for EXP-0024 — per-sample threshold map (detection/recall-only).
# Reproduces the sweep: 3 samples x 5 pcts x 10 frames (t=20..29) with frozen
# DoG sigmas, match vs GT via match_nodes, write metrics.json.
# CPU-only, deterministic. Exits 0 (verdict lives in metrics.json).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0024] sweeping 3 samples x 5 pcts x t=20..29 (~7 min CPU)..."
python3 "$EXP_DIR/sweep.py"
echo "[EXP-0024] OK: metrics.json written."
