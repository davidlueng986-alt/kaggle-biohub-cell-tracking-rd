#!/usr/bin/env bash
# Harvest v11 UNet kernel outputs into data/weights (idempotent, v10-safe).
# Usage: ./scripts/harvest_v11.sh
# - Downloads kernel outputs to data/weights/v11/ (raw, untouched).
# - Copies best/last ckpts to data/weights/unet_v11_best.pt + unet_v11_last.pt.
# - NEVER touches existing v10 files (unet_best.pt, unet_v10_*.pt).
# - Safe to re-run: only v11-named targets are written; no deletes.
# - Run ONLY after the v11 kernel COMPLETES on Kaggle GPU (weights don't exist yet).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL="liangwanyiudavid/biohub-unet-train-v11"
RAW_DIR="$ROOT/data/weights/v11"
BEST_DST="$ROOT/data/weights/unet_v11_best.pt"
LAST_DST="$ROOT/data/weights/unet_v11_last.pt"

fail() { echo "harvest_v11: FAIL: $*" >&2; exit 1; }

echo "harvest_v11: kernel=$KERNEL"
echo "harvest_v11: raw_dir=$RAW_DIR"

command -v kaggle >/dev/null 2>&1 || fail "kaggle CLI not found (needs network + credentials; run from a later stage)"

mkdir -p "$RAW_DIR"
kaggle kernels output "$KERNEL" -p "$RAW_DIR"
echo "harvest_v11: download OK; raw outputs:"
ls -la "$RAW_DIR"

# Promote raw ckpts to versioned v11 names. Only v11 paths are ever written.
promote() { # $1 = source basename, $2 = dest path
  local src="$RAW_DIR/$1" dst="$2"
  if [[ ! -f "$src" ]]; then
    echo "harvest_v11: WARN: missing $src (kernel may not have produced it yet); skipping"
    return 0
  fi
  if [[ -e "$dst" ]] && cmp -s "$src" "$dst"; then
    echo "harvest_v11: up-to-date $dst (identical; no copy needed)"
    return 0
  fi
  cp -f "$src" "$dst"
  echo "harvest_v11: wrote $dst"
}

promote "unet_best.pt" "$BEST_DST"
promote "unet_last.pt" "$LAST_DST"

echo "harvest_v11: weights dir (v10 files untouched):"
ls -la "$ROOT/data/weights/"

echo "harvest_v11: det/frame sanity reminder: EXP-0061 bar needs edge_raw>0 AND"
echo "harvest_v11: edge_adj>0 on >=1 window AND det/frame<=500 (defaults --thr 0.5"
echo "harvest_v11: --top-k 150 --max-det-per-frame 300 --ceiling 500)."
echo "harvest_v11: next command:"
echo "harvest_v11:   V11_WEIGHTS=data/weights/unet_v11_best.pt bash experiments/EXP-0061/run.sh"
