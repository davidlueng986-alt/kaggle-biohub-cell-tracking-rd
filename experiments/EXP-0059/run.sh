#!/usr/bin/env bash
# Runner for EXP-0059 — nested binary-darkness rule (PROTOCOL v1.2).
# brightness -> detect-missing (<=300f) -> link+score -> metrics.json.
# Exits 0; verdict in metrics.json.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
echo "[EXP-0059] step 1/3 brightness..."
python3 "$EXP_DIR/brightness.py"
echo "[EXP-0059] step 2/3 fresh detection (cap 300 frames)..."
python3 "$EXP_DIR/detect_missing.py"
echo "[EXP-0059] step 3/3 link (gate 7) + score (v1.1.0)..."
python3 "$EXP_DIR/link_score.py"
echo "[EXP-0059] OK: metrics.json written."
