#!/usr/bin/env bash
# Runner for EXP-0034 — per-sample-best transfer test (full-video, 3 samples).
# CPU-only, deterministic. Exits 0 (verdict lives in metrics.json even if STOP).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0034] full-video detect 3 samples x 100 frames + link + score..."
python3 "$EXP_DIR/transfer.py"
echo "[EXP-0034] OK: metrics.json written."
