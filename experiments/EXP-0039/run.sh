#!/usr/bin/env bash
# Runner for EXP-0039 — 05db0fb1 full-video @96.0 recall-vs-count-cost test.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
# Pipeline: detect (100 frames @96.0) -> global re-id + link -> score -> metrics.json
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05db0fb1"
PCT="96.0"

echo "[EXP-0039] 1/4: detect $SID t=0..99 @ $PCT ..."
for t in $(seq 0 99); do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct "$PCT" --out "$EXP_DIR/full_${SID}_t${t}.json" > /dev/null
done
echo "  detect done: $(ls "$EXP_DIR"/full_${SID}_t*.json | wc -l) frames"

echo "[EXP-0039] 2/4: global re-id + link (baseline_link defaults, gate 7um) ..."
python3 - "$EXP_DIR" "$ROOT" "$SID" <<'EOF'
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
pred = BL.link({"nodes": nodes, "edges": []})  # defaults: MAXD=7.0 um gate
json.dump(pred, open(os.path.join(d, f"{sid}_pred.json"), "w"))
print(f"  linked: {len(nodes)} nodes gid-unique, {len(pred['edges'])} edges "
      f"[{pred.get('assign')}]", flush=True)
EOF

echo "[EXP-0039] 3/4: score @96.0 + rescore @98.5 baseline ..."
python3 -u "$EXP_DIR/score_fast.py"

echo "[EXP-0039] 4/4: assemble metrics.json (comparison + verdict) ..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sc = json.load(open(os.path.join(d, "scores.json")))["p96"]
base = json.load(open(os.path.join(
    root, "experiments/EXP-0021/metrics.json")))["per_sample"]["6bba_05db0fb1"]
row96 = {"recall": sc["recall"], "det_f": sc["det_f"], "gid": sc["gid"],
         "raw": sc["raw"], "edge_adj": sc["edge"], "div": sc["div"],
         "score": sc["score"], "ec": sc["ec"], "dc": sc["dc"],
         "T_true": sc["T_true"], "T_ratio": sc["T_ratio"], "s_f": sc["s_f"],
         "assign": sc["assign"]}
row98 = {"recall": base["recall"], "det_f": base["det_f"],
         "raw": base["raw"], "edge_adj": base["edge"], "div": base["div"],
         "score": base["score"], "ec": base["ec"], "dc": base["dc"],
         "T_true": base["T_true"], "T_ratio": base["T_ratio"],
         "s_f": base["s_f"], "assign": base["assign"]}
rec_up = row96["recall"] > row98["recall"]
adj_up = row96["edge_adj"] > row98["edge_adj"]
verdict = "GO" if (rec_up and adj_up) else ("MIXED" if rec_up else "FAIL")
metrics = {
    "exp_id": "EXP-0039",
    "title": "05db0fb1 full-video @96.0 recall-vs-count-cost test",
    "hypothesis_id": "H-002-followup",
    "protocol_version": "1.1",
    "scorer_version": "1.1.0",
    "dry_run": False, "real_data": True, "image_based": True,
    "simplified_scorer": False,
    "sample": "6bba_05db0fb1", "frames": 100, "pct96": 96.0, "pct98": 98.5,
    "linker": "baseline_link defaults (gate 7um, one-to-one, causal)",
    "comparison": {
        "@96.0": row96,
        "@98.5_baseline_rescored": row98,
        "delta_recall": row96["recall"] - row98["recall"],
        "delta_raw": row96["raw"] - row98["raw"],
        "delta_adj": row96["edge_adj"] - row98["edge_adj"],
        "delta_score": row96["score"] - row98["score"],
        "delta_T_ratio": row96["T_ratio"] - row98["T_ratio"],
    },
    "verdict": verdict,
    "verdict_reason": (f"recall {'up' if rec_up else 'DOWN'} "
                       f"({row96['recall']:.4f} vs {row98['recall']:.4f}) AND "
                       f"adj {'up' if adj_up else 'DOWN'} "
                       f"({row96['edge_adj']:.4f} vs {row98['edge_adj']:.4f})"),
    "division_readout": ("div 0.0 both arms, dc 0/0/3: one-to-one linker "
                         "predicts zero forks; 3 GT divisions all FN as expected"),
    "parity_watch": (f"T_ratio @96.0 = {row96['T_ratio']:.4f} "
                     "(watch level ~0.65; below parity, adjustment bonus applies)"),
    "status": "done",
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0039] verdict={verdict} "
      f"d_recall={metrics['comparison']['delta_recall']:+.4f} "
      f"d_adj={metrics['comparison']['delta_adj']:+.4f}")
EOF
echo "[EXP-0039] OK: metrics.json written."
