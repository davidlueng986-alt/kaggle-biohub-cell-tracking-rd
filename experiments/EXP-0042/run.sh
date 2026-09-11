#!/usr/bin/env bash
# Runner for EXP-0042 — higher-moment DoG shape descriptors (ANALYSIS ONLY).
# 20 fresh @98.5 detects (2 missing samples x t20-29) + moments.py analysis.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if STOP).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0042] 1/2: fresh @98.5 window detects (missing combos only)..."
for sid in 44b6_0b24845f 44b6_0c582fdc; do
  for t in 20 21 22 23 24 25 26 27 28 29; do
    python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
      --t "$t" --pct 98.5 --out "$EXP_DIR/det98_${sid}_t${t}.json" > /dev/null
  done
  echo "  $sid @98.5 t20-29 done"
done

echo "[EXP-0042] 2/2: higher-moment analysis..."
python3 "$EXP_DIR/moments.py"
echo "[EXP-0042] OK: metrics.json written."
python3 -c "import json;m=json.load(open('$EXP_DIR/metrics.json'));print('[EXP-0042] verdict=%s best=%s' % (m['verdict'], m['best_stat']))"
