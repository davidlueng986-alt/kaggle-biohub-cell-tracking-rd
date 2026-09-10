#!/usr/bin/env bash
# Runner for EXP-0030 — Min-size ablation (@98.5, min_size in {25,50,100}).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05b6850b"
BLOCKS="20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49"

echo "[EXP-0030] 1/2: window detection across min-size configs (60 frame-runs)..."
for t in $BLOCKS; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --min-size 25 \
    --out "$EXP_DIR/ms25_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --min-size 50 \
    --out "$EXP_DIR/ms50_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --min-size 100 \
    --out "$EXP_DIR/ms100_t${t}.json" > /dev/null
done
echo "  detection done"

echo "[EXP-0030] 2/2: link blocks + score + verdict..."
python3 - "$EXP_DIR" "$ROOT" $BLOCKS <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3:]]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
gt_full = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in frames}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in frames],
        "edges": [e for e in gt_full["edges"] if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(frames) / 100)}
print(f"  GT subgraph: {len(gsub['nodes'])} nodes {len(gsub['edges'])} edges T~{gsub['T_true']}")
res = {}
for cfg in ("ms25", "ms50", "ms100"):
    nodes, gid = [], 0
    rec_n = rec_d = 0
    per_frame = {}
    for t in frames:
        det = json.load(open(os.path.join(d, f"{cfg}_t{t}.json")))
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        _, g2p = match_nodes(det["nodes"], g)
        rec_n += len(g2p); rec_d += len(g)
        per_frame[str(t)] = {"n_det": len(det["nodes"]), "n_gt": len(g),
                             "n_matched": len(g2p),
                             "recall": (len(g2p) / len(g)) if g else None}
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    pred = BL.link({"nodes": nodes, "edges": []})
    agg = score_samples([(cfg, pred, gsub, None)])
    s = agg["per_sample"][0]
    res[cfg] = {"min_size": int(cfg[2:]), "pct": 98.5,
                "recall": rec_n / rec_d, "n_det": len(nodes),
                "per_frame": per_frame,
                "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
                "ec": s["edge_counts"], "phased": pred.get("phased")}
    print(f"  {cfg}: rec={rec_n/rec_d:.4f} det={len(nodes)} "
          f"raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
base = res["ms50"]
print(f"  reference ms50(=A): rec={base['recall']:.4f} raw={base['raw']:.4f} adj={base['adj']:.4f}")
winners = [c for c in ("ms25", "ms100")
           if all([res[c]["recall"] >= base["recall"] - 1e-12,
                   res[c]["raw"] >= base["raw"] - 1e-12,
                   res[c]["adj"] >= base["adj"] - 1e-12])]
go = len(winners) > 0
metrics = {"exp_id": "EXP-0030", "title": "Min-size ablation",
           "hypothesis_id": "H-minsize", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "blocks": frames, "pct": 98.5,
           "configs": res,
           "reference": "ms50",
           "gate_any_ge_A": bool(go), "winners": winners,
           "decision": "go-full-video" if go else "stop",
           "decision_reason": ("Window gate " + ("PASS: " + ",".join(winners) + ">=ms50(A) on recall+raw+adj -> recommend EXP-0033 full-video GO (not run here)." if go else "FAIL: neither ms25 nor ms100 matches-or-beats ms50(A) on all of recall/raw/adj -> min-size stays 50; STOP, no full-video commit."))}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("gate any>=A:", go, winners if go else "")
if not go: print("STOP (recorded): min-size stays 50")
EOF
echo "[EXP-0030] OK: metrics.json written."
