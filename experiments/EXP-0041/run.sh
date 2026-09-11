#!/usr/bin/env bash
# Runner for EXP-0041 — window-best full-video validation
# (44b6_0b24845f @ 98.5, 44b6_0c582fdc @ 97.5, all 100 frames each).
# CPU-only, deterministic. Exits 0 (verdict lives in metrics.json even if STOP).
# Pipeline: detect (2x100 CLI) -> global re-id + link -> score.py CLI ->
#   rescore EXP-0040 @96 bars (read-only) -> metrics.json assembly.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

declare -A PCT=( [44b6_0b24845f]="98.5" [44b6_0c582fdc]="97.5" )
SIDS="44b6_0b24845f 44b6_0c582fdc"

echo "[EXP-0041] 1/4: detect 2 samples x 100 frames at window-best pct ..."
for sid in $SIDS; do
  p="${PCT[$sid]}"
  for t in $(seq 0 99); do
    python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
      --t "$t" --pct "$p" --out "$EXP_DIR/full_${sid}_t${t}.json" > /dev/null
  done
  echo "  $sid @$p done: $(ls "$EXP_DIR"/full_${sid}_t*.json | wc -l) frames"
done

echo "[EXP-0041] 2/4: global re-id + link per video (baseline_link defaults, gate 7um) ..."
python3 - "$EXP_DIR" "$ROOT" $SIDS <<'EOF'
import json, os, sys
d, root, sids = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
for sid in sids:
    nodes, gid = [], 0
    for t in range(100):
        det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    pred = BL.link({"nodes": nodes, "edges": []})  # defaults: MAXD=7.0 um gate
    json.dump(pred, open(os.path.join(d, f"{sid}_pred.json"), "w"))
    print(f"  linked {sid}: {len(nodes)} nodes gid-unique, "
          f"{len(pred['edges'])} edges [{pred.get('assign')}]", flush=True)
EOF

echo "[EXP-0041] 3/4: score via trusted score.py CLI + rescore frozen EXP-0040 @96 bars ..."
for sid in $SIDS; do
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/${sid}_pred.json" \
    --gt "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" \
    --out "$EXP_DIR/${sid}_scores.json" > /dev/null
  echo "  scored $sid"
  python3 "$ROOT/scripts/score.py" \
    --pred "$ROOT/experiments/EXP-0040/${sid}_pred.json" \
    --gt "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" \
    --out "$EXP_DIR/${sid}_bar96_scores.json" > /dev/null
  echo "  rescored bar $sid (@96 frozen pred)"
done

echo "[EXP-0041] 4/4: assemble metrics.json (recall diagnostic + verdicts) ..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
import numpy as np
from scipy.optimize import linear_sum_assignment as lsa
d, root = sys.argv[1], sys.argv[2]

WIN_RECALL = {"44b6_0b24845f": 0.8, "44b6_0c582fdc": 0.5}  # EXP-0024 t20-29 refs
WIN_PCT = {"44b6_0b24845f": 98.5, "44b6_0c582fdc": 97.5}
VX = (1.625, 0.40625, 0.40625)

def frame_recall(det_nodes, gt_nodes_t):
    n, m = len(det_nodes), len(gt_nodes_t)
    if n == 0 or m == 0:
        return 0.0
    C = np.zeros((n, m))
    for i, p in enumerate(det_nodes):
        for j, g in enumerate(gt_nodes_t):
            dz = (p["z"] - g["z"]) * VX[0]
            dy = (p["y"] - g["y"]) * VX[1]
            dx = (p["x"] - g["x"]) * VX[2]
            C[i, j] = (dz * dz + dy * dy + dx * dx) ** 0.5
    ri, ci = lsa(C)
    return float(sum(1 for r, c in zip(ri, ci) if C[r, c] <= 7.0)) / m

per, n_hold = {}, 0
for sid in ("44b6_0b24845f", "44b6_0c582fdc"):
    gt = json.load(open(os.path.join(
        root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    gt_by_t = {}
    for n_ in gt["nodes"]:
        gt_by_t.setdefault(int(n_["t"]), []).append(n_)
    det_total, times, recs = 0, [], []
    for t in range(100):
        det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
        times.append(det["params"]["elapsed_s"])
        det_total += len(det["nodes"])
        g = gt_by_t.get(t, [])
        if g:
            recs.append(frame_recall(det["nodes"], g))
    full_recall = sum(recs) / len(recs) if recs else 0.0
    s = json.load(open(os.path.join(d, f"{sid}_scores.json")))
    ps = s["per_sample"][0]
    b = json.load(open(os.path.join(d, f"{sid}_bar96_scores.json")))
    bs = b["per_sample"][0]
    bar_adj, bar_raw = bs["adjusted_edge_jaccard"], bs["edge_jaccard_raw"]
    full_adj, full_raw = ps["adjusted_edge_jaccard"], ps["edge_jaccard_raw"]
    d_rec = full_recall - WIN_RECALL[sid]
    d_adj = full_adj - bar_adj
    ok_rec = d_rec >= -0.10
    ok_adj = d_adj >= -0.10
    holds = bool(ok_rec and ok_adj)
    n_hold += int(holds)
    per[sid] = {
        "pct": WIN_PCT[sid],
        "window_recall_ref": WIN_RECALL[sid],
        "full_recall": full_recall,
        "d_recall_full_minus_window": d_rec,
        "recall_within_0.10": bool(ok_rec),
        "bar": "EXP-0040 @96.0 frozen pred, recomputed-by-rescoring (never pasted)",
        "bar96_adj_rescored": bar_adj,
        "bar96_raw_rescored": bar_raw,
        "bar96_T_pred": bs["T_pred"],
        "bar96_T_true": bs["T_true"],
        "full_edge_adj": full_adj,
        "full_edge_raw": full_raw,
        "d_adj_full_minus_bar": d_adj,
        "adj_within_0.10_of_bar": bool(ok_adj),
        "full_edge_counts": ps["edge_counts"],
        "full_division_counts": ps["division_counts"],
        "full_division_jaccard": ps["division_jaccard"],
        "full_score": ps["score"],
        "full_T_pred": ps["T_pred"],
        "full_T_true": ps["T_true"],
        "det_per_frame": det_total / 100,
        "total_det": det_total,
        "s_per_frame": sum(times) / len(times),
        "n_gt_frames": len(recs),
        "verdict": "HOLDS" if holds else "BREAKS",
        "verdict_reason": (
            f"recall {full_recall:.4f} vs window {WIN_RECALL[sid]:.4f} "
            f"(d={d_rec:+.4f}, need >=-0.10) AND adj {full_adj:.4f} vs bar "
            f"{bar_adj:.4f} (d={d_adj:+.4f}, need >=-0.10)"),
    }

overall = "GO" if n_hold == 2 else "STOP"
metrics = {
    "exp_id": "EXP-0041",
    "title": "Window-best full-video validation 98.5/97.5",
    "protocol_version": "1.1",
    "samples": ["44b6_0b24845f", "44b6_0c582fdc"],
    "frames": 100,
    "linker": "baseline_link defaults (gate 7um, one-to-one, causal)",
    "scorer": "scripts/score.py CLI v1.1.0, scripts unmodified; "
              "recall diagnostic via scipy LSA (diagnostic only)",
    "per_sample": per,
    "overall": overall,
    "overall_reason": (f"{n_hold}/2 HOLDS: " + ", ".join(
        f"{k}={v['verdict']}" for k, v in per.items())),
    "policy_note": ("GO -> window-best levels viable; recommend per-sample "
                    "policy rung (do not run). STOP -> window does not transfer."),
    "status": "done",
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0041] overall={overall} "
      + " ".join(f"{k}={v['verdict']}" for k, v in per.items()))
EOF
echo "[EXP-0041] OK: metrics.json written."
