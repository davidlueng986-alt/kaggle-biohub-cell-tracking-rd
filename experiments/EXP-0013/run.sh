#!/usr/bin/env bash
# Runner for EXP-0013 — window gate with edge readout (D vs A/B/C).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05b6850b"
BLOCKS="20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49"

echo "[EXP-0013] 1/2: window detection across configs..."
for t in $BLOCKS; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --out "$EXP_DIR/A_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.0 --split-size 3000 \
    --out "$EXP_DIR/B_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.0 --split-size 3000 --prominence 0.7 \
    --out "$EXP_DIR/C_t${t}.json" > /dev/null
done
echo "  detection done"

echo "[EXP-0013] 2/2: link blocks + score + verdict..."
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
for cfg in ("A", "B", "C"):
    nodes, gid, ns = [], 0, 0
    rec_n = rec_d = 0
    for t in frames:
        det = json.load(open(os.path.join(d, f"{cfg}_t{t}.json")))
        ns += det["params"].get("n_split", 0)
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        _, g2p = match_nodes(det["nodes"], g)
        rec_n += len(g2p); rec_d += len(g)
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"],
                          "split": n.get("split", False)})
    phased = False  # A/B/C link without flags (legacy path); D below uses flags
    use = [{"id": n["id"], "t": n["t"], "z": n["z"], "y": n["y"], "x": n["x"]} for n in nodes]
    pred = BL.link({"nodes": use, "edges": []})
    agg = score_samples([(f"{cfg}", pred, gsub, None)])
    s = agg["per_sample"][0]
    res[cfg] = {"recall": rec_n / rec_d, "n_det": len(nodes), "n_splits": ns,
                "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
                "ec": s["edge_counts"], "phased": pred.get("phased")}
    print(f"  {cfg}: rec={rec_n/rec_d:.3f} det={len(nodes)} splits={ns} "
          f"raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
# D: C detections WITH split flags -> two-phase linking
nodes, gid = [], 0
for t in frames:
    det = json.load(open(os.path.join(d, f"C_t{t}.json")))
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"],
                      "split": n.get("split", False)})
pred = BL.link({"nodes": nodes, "edges": []})
assert pred.get("phased") is True, "D must engage two-phase path"
agg = score_samples([("D", pred, gsub, None)])
s = agg["per_sample"][0]
g = [n for n in gt_full["nodes"] if n["t"] in frames]
# recall for D (same detections as C)
res["D"] = {"recall": res["C"]["recall"], "n_det": len(nodes),
            "n_splits": res["C"]["n_splits"],
            "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
            "ec": s["edge_counts"], "phased": True}
print(f"  D: rec={res['D']['recall']:.3f} det={len(nodes)} raw={s['edge_jaccard_raw']:.4f} "
      f"adj={s['adjusted_edge_jaccard']:.4f} ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} (phased)")
base = res["A"]
go = all([res["D"]["recall"] >= base["recall"] - 1e-12,
          res["D"]["raw"] >= base["raw"] - 1e-12,
          res["D"]["adj"] >= base["adj"] - 1e-12])
metrics = {"exp_id": "EXP-0013", "title": "Prominence-gated splits + conservative linking",
           "hypothesis_id": "H-002", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "blocks": frames, "configs": res,
           "gate_D_ge_A": bool(go),
           "decision": "keep-trying",
           "decision_reason": ("Window gate " + ("PASS: D>=A on recall+raw+adj -> EXP-0014 full-video GO." if go else "FAIL: gated splitting does not pay on window -> splitter family parked; pivot to dim-cell scale terms / H-003 appearance.") + " Ceiling keep-trying (window rung).")}
assert True  # ledger records negative gates too; verdict in gate_D_ge_A
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("gate D>=A:", go)
if not go: print("STOP (recorded): no full-video commit")
EOF
echo "[EXP-0013] OK: metrics.json written."
