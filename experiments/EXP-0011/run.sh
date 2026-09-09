#!/usr/bin/env bash
# Runner for EXP-0011 — full-video 6bba@98.0.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05b6850b"

echo "[EXP-0011] 1/2: full-video detection @98.0 + link + score..."
for t in $(seq 0 99); do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.0 --out "$EXP_DIR/full_t${t}.json" > /dev/null
done
echo "  detection done"
python3 - "$EXP_DIR" "$ROOT" "$SID" <<'EOF'
import json, os, sys
d, root, sid = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
nodes, gid = [], 0
for t in range(100):
    det = json.load(open(os.path.join(d, f"full_t{t}.json")))
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
pred = BL.link({"nodes": nodes, "edges": []})
json.dump(pred, open(os.path.join(d, "full_pred.json"), "w"))
print(f"  {sid}: {len(nodes)} detections -> {len(pred['edges'])} links [{pred.get('assign')}]")
EOF
python3 "$ROOT/scripts/score.py" \
  --pred "$EXP_DIR/full_pred.json" \
  --gt "$ROOT/experiments/EXP-0003/gt/${SID}_gt.json" \
  --out "$EXP_DIR/full_scores.json" > /dev/null

echo "[EXP-0011] 2/2: verdict vs @98.5..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
sys.path.insert(0, os.path.join(d, "..", "..", "scripts"))
from score import match_nodes
sid = "6bba_05b6850b"
gt_full = json.load(open(os.path.join(d, "..", "EXP-0003", "gt", f"{sid}_gt.json")))
s = json.load(open(os.path.join(d, "full_scores.json")))["per_sample"][0]
rec_all, times, counts = [], [], []
for t in range(100):
    det = json.load(open(os.path.join(d, f"full_t{t}.json")))
    times.append(det["params"]["elapsed_s"])
    counts.append(len(det["nodes"]))
    g = [n for n in gt_full["nodes"] if n["t"] == t]
    if g:
        _, g2p = match_nodes(det["nodes"], g)
        rec_all.append(len(g2p) / len(g))
rec = sum(rec_all) / len(rec_all)
row = {"recall_full": rec, "det_per_frame": sum(counts) / len(counts),
       "n_det_total": sum(counts), "T_ratio": sum(counts) / s["T_true"],
       "edge_raw": s["edge_jaccard_raw"], "edge_adj": s["adjusted_edge_jaccard"],
       "div": s["division_jaccard"], "score": s["score"],
       "ec": s["edge_counts"], "dc": s["division_counts"], "T_true": s["T_true"],
       "s_per_frame": sum(times) / len(times)}
ref_adj, ref_rec = 0.8194, 0.893  # EXP-0009 6bba@98.5
checks = {"recall_ge_0.95": rec >= 0.95, "adj_ge_985": s["adjusted_edge_jaccard"] >= ref_adj - 1e-12}
metrics = {"exp_id": "EXP-0011", "title": "Full-video 6bba@98.0",
           "hypothesis_id": "H-002", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "row": row, "ref_985": {"recall": ref_rec, "adj": ref_adj},
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("@98.0 verdict per checks; 44b6 untouched (locked @99.0). "
                               "Single deterministic run ceiling holds regardless.")}
assert True  # ledger records falsified runs too; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"  {sid}@98.0: recall={rec:.3f} det/f={row['det_per_frame']:.0f} T_ratio={row['T_ratio']:.2f} "
      f"raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} (ref {ref_adj}) "
      f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
print("checks:", checks)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0011] OK: metrics.json written."
