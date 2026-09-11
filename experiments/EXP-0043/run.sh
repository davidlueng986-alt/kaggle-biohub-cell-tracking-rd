#!/usr/bin/env bash
# Runner for EXP-0043 — 062c8d37 full-video @96.0 replication of EXP-0039.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
# Pipeline: detect (100 frames @96.0) -> global re-id + link -> score -> metrics.json
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_062c8d37"
PCT="96.0"

echo "[EXP-0043] 1/4: detect $SID t=0..99 @ $PCT ..."
for t in $(seq 0 99); do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct "$PCT" --out "$EXP_DIR/full_${SID}_t${t}.json" > /dev/null
done
echo "  detect done: $(ls "$EXP_DIR"/full_${SID}_t*.json | wc -l) frames"

echo "[EXP-0043] 2/4: global re-id + link (baseline_link defaults, gate 7um) ..."
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

echo "[EXP-0043] 3/4: score @96.0 + rescore @98.5 baseline ..."
python3 -u "$EXP_DIR/score_run.py"

echo "[EXP-0043] 4/4: assemble metrics.json (comparison + verdict) ..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sc = json.load(open(os.path.join(d, "scores.json")))
r96, r98 = sc["p96"], sc["p98"]
row96 = {"recall": r96["recall"], "det_f": r96["det_f"], "gid": r96["gid"],
         "raw": r96["raw"], "edge_adj": r96["edge"], "div": r96["div"],
         "score": r96["score"], "ec": r96["ec"], "dc": r96["dc"],
         "T_true": r96["T_true"], "T_pred": r96["T_pred"],
         "T_ratio": r96["T_ratio"], "s_f": r96["s_f"], "assign": r96["assign"]}
row98 = {"raw": r98["raw"], "edge_adj": r98["edge"], "div": r98["div"],
         "score": r98["score"], "ec": r98["ec"], "dc": r98["dc"],
         "T_true": r98["T_true"], "T_pred": r98["T_pred"],
         "T_ratio": r98["T_ratio"]}
# @98.5 recall/det_f/s_f bar from frozen EXP-0021 metrics (detection-level
# diagnostics the rescore does not recompute; rescore covers raw/adj/div).
m21 = json.load(open(os.path.join(
    root, "experiments/EXP-0021/metrics.json")))["per_sample"]["6bba_062c8d37"]
row98["recall"] = m21["recall"]
row98["det_f"] = m21["det_f"]
row98["s_f"] = m21["s_f"]
row98["assign"] = m21["assign"]
rec_ok = row96["recall"] >= 0.90
adj_ok = row96["edge_adj"] >= row98["edge_adj"]
verdict = ("REPLICATES" if (rec_ok and adj_ok)
           else ("DIVERGES" if (not rec_ok and not adj_ok) else "MIXED"))
policy = ("GO (@96-as-dense-policy)" if verdict == "REPLICATES"
          else "STOP (sample luck)")
metrics = {
    "exp_id": "EXP-0043",
    "title": "062c8d37 full-video @96.0 replication of EXP-0039",
    "hypothesis_id": "H-002-followup",
    "protocol_version": "1.1",
    "scorer_version": sc["scorer"]["scorer_version"],
    "dry_run": False, "real_data": True, "image_based": True,
    "simplified_scorer": False,
    "sample": "6bba_062c8d37", "frames": 100, "pct96": 96.0, "pct98": 98.5,
    "linker": "baseline_link defaults (gate 7um, one-to-one, causal)",
    "comparison": {
        "@96.0": row96,
        "@98.5_baseline_rescored": row98,
        "delta_recall": row96["recall"] - row98["recall"],
        "delta_raw": row96["raw"] - row98["raw"],
        "delta_adj": row96["edge_adj"] - row98["edge_adj"],
        "delta_score": row96["score"] - row98["score"],
        "delta_T_ratio": row96["T_ratio"] - row98["T_ratio"],
        "delta_div": row96["div"] - row98["div"],
    },
    "gates": {"recall_ge_0.90": rec_ok,
              "adj_ge_bar": adj_ok,
              "bar_adj": row98["edge_adj"]},
    "verdict": verdict,
    "verdict_reason": (f"recall {'PASS' if rec_ok else 'FAIL'} "
                       f"({row96['recall']:.4f} vs 0.90 gate) AND adj "
                       f"{'PASS' if adj_ok else 'FAIL'} ({row96['edge_adj']:.4f} "
                       f"vs bar {row98['edge_adj']:.4f})"),
    "policy": policy,
    "division_readout": (f"div {row96['div']:.4f} @96 vs {row98['div']:.4f} @98.5; "
                         f"dc96={row96['dc']} dc98={row98['dc']}: one-to-one linker "
                         f"predicts zero forks; the 1 GT division FN as expected"),
    "status": "done",
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0043] verdict={verdict} policy={policy} "
      f"d_recall={metrics['comparison']['delta_recall']:+.4f} "
      f"d_adj={metrics['comparison']['delta_adj']:+.4f}")
EOF
echo "[EXP-0043] OK: metrics.json written."
