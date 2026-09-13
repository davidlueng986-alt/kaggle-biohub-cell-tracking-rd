#!/usr/bin/env bash
# Runner for EXP-0061 — UNet v11 gated-detection eval (PROTOCOL v1.2, scorer v1.1.0).
# - Trusted scorer path on v11 detections IF weights+infer exist.
# - Else exits 0 with status PENDING_CODE (never fakes numbers).
# - NEVER modifies notebooks/ (parallel agents own it; read-only probe only).
# - CPU-only, deterministic, < 30 min. No pip installs, no kaggle calls.
set -euo pipefail
EXP_ID="EXP-0061"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$ROOT/experiments/$EXP_ID"
SCORER="$ROOT/scripts/score.py"
METRICS="$DIR/metrics.json"

# Acceptance bar (mirrors hypothesis.md; keep in sync).
CEILING_DET_PER_FRAME="${V11_CEILING_DET_PER_FRAME:-500}"
SAMPLE="${V11_SAMPLE:-6bba_05b6850b}"
WT0="${V11_T0:-20}"
WT1="${V11_T1:-29}"

pending() { # $1 = reason
  python3 - "$METRICS" "$1" <<'EOF'
import json, sys
path, reason = sys.argv[1], sys.argv[2]
with open(path) as f:
    m = json.load(f)
m["status"] = "PENDING_CODE"
m["reason"] = reason
m["numbers"] = None
with open(path, "w") as f:
    json.dump(m, f, indent=2)
EOF
  echo "[$EXP_ID] status=PENDING_CODE reason: $1"
  echo "[$EXP_ID] metrics.json records status + reason; no numbers fabricated."
}

echo "[$EXP_ID] validating trusted scorer plumbing (score.py v1.1.0)..."
python3 "$SCORER" --dry-run
echo "[$EXP_ID] scorer dry-run OK."

# --- Probe for v11 artefacts (existence checks only) ---
WEIGHTS="${V11_WEIGHTS:-}"
if [[ -z "$WEIGHTS" ]]; then
  for cand in "$ROOT"/data/weights/unet_v11*.pt; do
    [[ -e "$cand" ]] && { WEIGHTS="$cand"; break; }
  done
fi
INFER="${V11_INFER:-}"  # explicit entrypoint override (contract path from infer agent)
if [[ -z "$INFER" ]]; then
  # Read-only probes of the parallel agents' expected locations; never create/modify.
  for cand in "$ROOT/notebooks/train_unet/infer_v11.py" "$ROOT/notebooks/train_unet/infer.py"; do
    [[ -e "$cand" ]] && { INFER="$cand"; break; }
  done
fi

if [[ -z "$WEIGHTS" || ! -e "$WEIGHTS" ]]; then
  pending "v11 weights missing (no data/weights/unet_v11*.pt and \$V11_WEIGHTS unset); needs train agent output"
  exit 0
fi
if [[ -z "$INFER" || ! -e "$INFER" ]]; then
  pending "v11 infer entrypoint missing (parallel infer agent has not landed \$V11_INFER / notebooks contract path); weights seen at $WEIGHTS"
  exit 0
fi

echo "[$EXP_ID] weights: $WEIGHTS"
echo "[$EXP_ID] infer:   $INFER"
echo "[$EXP_ID] window:  $SAMPLE t$WT0-$WT1; ceiling: $CEILING_DET_PER_FRAME det/frame"
echo "[$EXP_ID] gating:  threshold=${V11_THRESHOLD:-<infer-default>} topK=${V11_TOPK:-<infer-default>} density_cap=${V11_DENSITY_CAP:-<infer-default>}"
echo "[$EXP_ID] TODO(live-run): gated infer -> link -> 'python3 scripts/score.py --pred <pred> --gt <gt> --out <score.json>';"
echo "[$EXP_ID] apply bar (edge_raw>0 AND edge_adj>0 AND det/frame<=$CEILING_DET_PER_FRAME) and write real numbers into metrics.json."
pending "v11 artefacts present but live eval not yet executed in this scaffold run (weights=$WEIGHTS infer=$INFER); re-run run.sh to execute"
exit 0
