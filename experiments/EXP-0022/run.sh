#!/usr/bin/env bash
# Runner for EXP-0022 — downsample parity + timing (MAD-pure pre-falsified at probe).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05b6850b"
BLOCKS="20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49"

echo "[EXP-0022] 1/2: window detection A (full) vs DS (half-res)..."
for t in $BLOCKS; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --out "$EXP_DIR/A_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --downsample 2 --out "$EXP_DIR/DS_t${t}.json" > /dev/null
done
echo "  detection done"

echo "[EXP-0022] 2/2: link + score + verdict..."
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
res = {}
for cfg, pat in (("A", "A_t{t}.json"), ("DS", "DS_t{t}.json")):
    nodes, gid, rec_n, rec_d, times = [], 0, 0, 0, []
    for t in frames:
        det = json.load(open(os.path.join(d, pat.format(t=t))))
        times.append(det["params"]["elapsed_s"])
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        _, g2p = match_nodes(det["nodes"], g)
        rec_n += len(g2p); rec_d += len(g)
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    pred = BL.link({"nodes": nodes, "edges": []})
    agg = score_samples([(cfg, pred, gsub, None)])
    s = agg["per_sample"][0]
    res[cfg] = {"recall": rec_n / rec_d, "n_det": len(nodes),
                "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
                "ec": s["edge_counts"], "s_f": sum(times) / len(times),
                "phased": pred.get("phased")}
    print(f"  {cfg}: rec={rec_n/rec_d:.3f} det={len(nodes)} raw={s['edge_jaccard_raw']:.4f} "
          f"adj={s['adjusted_edge_jaccard']:.4f} ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
          f"t={sum(times)/len(times):.2f}s/f", flush=True)
ref13 = json.load(open(os.path.join(d, "..", "EXP-0013", "metrics.json")))["configs"]["A"]
anchor = (abs(res["A"]["recall"] - 0.982 - 0.0) < 0.002 and abs(res["A"]["raw"] - ref13["raw"]) < 1e-12
          and res["A"]["ec"] == ref13["ec"])
print("  anchor A==EXP-0013A:", anchor)
a, w = res["A"], res["DS"]
go = (w["recall"] >= a["recall"] - 0.01 and w["raw"] >= a["raw"] - 0.005
      and w["adj"] >= a["adj"] - 0.005 and (a["s_f"] / w["s_f"]) >= 2.5)
metrics = {"exp_id": "EXP-0022", "title": "Downsample parity + timing paydown",
           "hypothesis_id": "H-002+H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "blocks": frames, "configs": res,
           "anchor_A_reproduced": bool(anchor),
           "speedup": round(a["s_f"] / w["s_f"], 2),
           "go_full_video": bool(go),
           "mad_probe": {"verdict": "falsified@probe", "note": "median+k*MAD sits at background (thr 4-8 vs 60): merges everything, recall 5-6/8 < 8/8. No window matrix spent."},
           "decision": "keep-trying",
           "decision_reason": ("Window verdict per gate; GO -> EXP-0023 full-video DS + kernel upgrade path. "
                               "Ceiling keep-trying (window rung).")}
assert anchor, "ANCHOR FAILED: A != EXP-0013 A"
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("GO:", go)
if not go: print("STOP (recorded): downsample loses too much")
EOF
echo "[EXP-0022] OK: metrics.json written."
