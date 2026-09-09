#!/usr/bin/env bash
# Runner for EXP-0009 — full-video @98.5 + count/edge tradeoff.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SAMPLES="44b6_0113de3b 6bba_05b6850b"

echo "[EXP-0009] 1/2: full-video detection @98.5 + link + score..."
for sid in $SAMPLES; do
  for t in $(seq 0 99); do
    python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
      --t "$t" --pct 98.5 --out "$EXP_DIR/full_${sid}_t${t}.json" > /dev/null
  done
  echo "  $sid detection done"
  python3 - "$EXP_DIR" "$ROOT" "$sid" <<'EOF'
import json, os, sys
d, root, sid = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
nodes, gid = [], 0
for t in range(100):
    det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
pred = BL.link({"nodes": nodes, "edges": []})
json.dump(pred, open(os.path.join(d, f"full_{sid}_pred.json"), "w"))
print(f"  {sid}: {len(nodes)} detections -> {len(pred['edges'])} links [{pred.get('assign')}]")
EOF
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/full_${sid}_pred.json" \
    --gt "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" \
    --out "$EXP_DIR/full_${sid}_scores.json" > /dev/null
done

echo "[EXP-0009] 2/2: tradeoff vs @99.0 + verdict..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
SIDS = ["44b6_0113de3b", "6bba_05b6850b"]
sys.path.insert(0, os.path.join(d, "..", "..", "scripts"))
from score import match_nodes
prev = json.load(open(os.path.join(d, "..", "EXP-0008", "metrics.json")))
rows = {}
for sid in SIDS:
    gt_full = json.load(open(os.path.join(d, "..", "EXP-0003", "gt", f"{sid}_gt.json")))
    agg = json.load(open(os.path.join(d, f"full_{sid}_scores.json")))
    s = agg["per_sample"][0]
    rec_all, times, counts = [], [], []
    for t in range(100):
        det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
        times.append(det["params"]["elapsed_s"])
        counts.append(len(det["nodes"]))
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        if g:
            _, g2p = match_nodes(det["nodes"], g)
            rec_all.append(len(g2p) / len(g))
    old = prev["full_video_p99"][sid]
    rows[sid] = {"recall_full": sum(rec_all) / len(rec_all),
                 "det_per_frame": sum(counts) / len(counts),
                 "n_det_total": sum(counts),
                 "edge_raw": s["edge_jaccard_raw"], "edge_adj": s["adjusted_edge_jaccard"],
                 "div": s["division_jaccard"], "score": s["score"],
                 "ec": s["edge_counts"], "dc": s["division_counts"],
                 "T_true": s["T_true"],
                 "T_ratio": sum(counts) / s["T_true"],
                 "s_per_frame": sum(times) / len(times)}
    # @99.0 reference numbers (EXP-0008 full section uses edge_adj/div)
    o = prev["full_video_p99"][sid]
    rows[sid]["old_adj"] = o["edge_adj"] if "edge_adj" in o else None
    print(f"  {sid}: recall={rows[sid]['recall_full']:.3f} det/f={rows[sid]['det_per_frame']:.0f} "
          f"T_ratio={rows[sid]['T_ratio']:.2f} raw={s['edge_jaccard_raw']:.4f} "
          f"adj={s['adjusted_edge_jaccard']:.4f} (was {rows[sid]['old_adj']}) "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
checks = {f"{sid}_recall_ge_0.95": rows[sid]["recall_full"] >= 0.95 for sid in SIDS}
checks.update({f"{sid}_adj_ge_99": rows[sid]["edge_adj"] >= rows[sid]["old_adj"] - 1e-12 for sid in SIDS})
metrics = {"exp_id": "EXP-0009", "title": "Full-video @98.5 + count/edge tradeoff",
           "hypothesis_id": "H-002", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "rows": rows, "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Operating-point selection rung (not promotion: single deterministic run). "
                               "@98.5 verdict per checks; T_ratio recorded for the bonus→penalty watch. "
                               "Next: per-sample levels if tradeoff splits, else H-003 appearance / H-005 timing.")}
assert True  # ledger records falsified runs too; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0009] OK: metrics.json written."
