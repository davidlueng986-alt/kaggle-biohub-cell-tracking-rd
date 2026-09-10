#!/usr/bin/env bash
# Runner for EXP-0035 — Learned-detector evaluation.
# Full eval: UNet heatmap infer (10-frame window) -> BL.link -> score vs GT.
set -euo pipefail

# --- weights config (set once unet_best.pt lands; empty = not landed) ---
WEIGHTS_PATH=""

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0035"

if [[ -z "${WEIGHTS_PATH}" ]]; then
  echo "[EXP-0035] weights not landed: set WEIGHTS_PATH at top of run.sh to unet_best.pt" >&2
  exit 2
fi
if [[ ! -f "${WEIGHTS_PATH}" ]]; then
  echo "[EXP-0035] weights not landed: file not found: ${WEIGHTS_PATH}" >&2
  exit 2
fi

SID="6bba_05b6850b"
T0=20
T1=29
DET="$EXP/det_${SID}_t${T0}-${T1}.json"
LINKED="$EXP/linked_${SID}_t${T0}-${T1}.json"
METRICS="$EXP/metrics.json"

echo "[EXP-0035] infer ${SID} t${T0}-${T1} ..."
python3 "$ROOT/notebooks/train_unet/infer.py" \
  --weights "$WEIGHTS_PATH" \
  --zarr "$ROOT/data/train/${SID}.zarr" \
  --t-start "$T0" --t-end "$T1" \
  --out "$DET"

echo "[EXP-0035] link + score ..."
WEIGHTS_PATH="$WEIGHTS_PATH" DET="$DET" LINKED="$LINKED" METRICS="$METRICS" \
SID="$SID" T0="$T0" T1="$T1" python3 - "$ROOT" <<'EOF'
import json
import os
import sys

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "notebooks", "train_unet"))
import baseline_link as BL
from score import match_nodes, score_single

SID, T0, T1 = os.environ["SID"], int(os.environ["T0"]), int(os.environ["T1"])
EXP = os.path.join(ROOT, "experiments", "EXP-0035")

det = json.load(open(os.environ["DET"]))
linked = BL.link({"nodes": det["nodes"], "edges": []})
json.dump(linked, open(os.environ["LINKED"], "w"))
print(f"linked: {len(linked['nodes'])} nodes -> {len(linked['edges'])} edges")


def window_graph(g):
    nodes = [n for n in g["nodes"] if T0 <= int(n["t"]) <= T1]
    ids = {n["id"] for n in nodes}
    edges = [e for e in g.get("edges", []) if e[0] in ids and e[1] in ids]
    return {"nodes": nodes, "edges": edges}


gt = window_graph(json.load(open(os.path.join(
    ROOT, "experiments", "EXP-0003", "gt", f"{SID}_gt.json"))))
dog = window_graph(json.load(open(os.path.join(
    ROOT, "experiments", "EXP-0009", f"full_{SID}_pred.json"))))
# NOTE: window-local scoring; full-video T_true does NOT apply to windows.
for g in (gt, dog, linked):
    g.pop("T_true", None)

p2g_l, g2p_l = match_nodes(linked["nodes"], gt["nodes"])
p2g_d, g2p_d = match_nodes(dog["nodes"], gt["nodes"])
rec_l = len(g2p_l) / max(len(gt["nodes"]), 1)
rec_d = len(g2p_d) / max(len(gt["nodes"]), 1)
s_l = score_single(linked, gt)
s_d = score_single(dog, gt)
gt_per_frame = len(gt["nodes"]) / (T1 - T0 + 1)
det_per_frame = len(linked["nodes"]) / (T1 - T0 + 1)

verdict = ("SIGNAL" if (rec_l > rec_d
                        and s_l["edge_jaccard_raw"] >= s_d["edge_jaccard_raw"]
                        and det_per_frame <= 2.0 * gt_per_frame)
           else "REJECT")
metrics = {
    "exp_id": "EXP-0035",
    "title": "Learned-detector evaluation",
    "status": "evaluated",
    "window": {"sample": SID, "t": [T0, T1]},
    "weights": os.environ["WEIGHTS_PATH"],
    "learned": {"recall": rec_l, "edge_raw": s_l["edge_jaccard_raw"],
                "edge_adj": s_l["adjusted_edge_jaccard"],
                "div": s_l["division_jaccard"], "score": s_l["score"],
                "det_per_frame": det_per_frame},
    "dog_window_bar": {"recall": rec_d, "edge_raw": s_d["edge_jaccard_raw"],
                       "edge_adj": s_d["adjusted_edge_jaccard"],
                       "div": s_d["division_jaccard"], "score": s_d["score"],
                       "det_per_frame": len(dog["nodes"]) / (T1 - T0 + 1)},
    "gt_per_frame": gt_per_frame,
    "verdict": verdict,
    "notes": ("window-local scoring (no T_true); DoG bar recomputed on same "
              "window from EXP-0009 reference; single deterministic pass"),
}
json.dump(metrics, open(os.environ["METRICS"], "w"), indent=2)
print(json.dumps(metrics, indent=2))
print(f"[EXP-0035] verdict: {verdict} (wrote {os.environ['METRICS']})")
EOF
