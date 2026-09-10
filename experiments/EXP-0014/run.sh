#!/usr/bin/env bash
# Runner for EXP-0014 — scale-fusion window gate with edge readout.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05b6850b"
SMALL="--sigma-small 0.7,2.0,2.0 --sigma-large 1.1,3.2,3.2"
BLOCKS="20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49"

echo "[EXP-0014] 1/2: window detection (base + small scales)..."
for t in $BLOCKS; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --out "$EXP_DIR/base85_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 $SMALL --out "$EXP_DIR/sm85_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.0 $SMALL --out "$EXP_DIR/sm80_t${t}.json" > /dev/null
done
echo "  detection done"

echo "[EXP-0014] 2/2: fuse + link + score + verdict..."
python3 - "$EXP_DIR" "$ROOT" $BLOCKS <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3:]]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
VX = (1.625, 0.40625, 0.40625)
gt_full = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in frames}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in frames],
        "edges": [e for e in gt_full["edges"] if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(frames) / 100)}

def um(a, b):
    dz, dy, dx = (a["z"]-b["z"])*VX[0], (a["y"]-b["y"])*VX[1], (a["x"]-b["x"])*VX[2]
    return (dz*dz + dy*dy + dx*dx) ** 0.5

def fuse(base, extra, gate=3.0):
    """Keep extra detections >= gate um from every base detection."""
    keep = []
    for w in extra:
        if all(um(w, v) >= gate for v in base):
            keep.append(w)
    return base + keep

def build(cfg):
    """cfg: A | B | C | D | E -> node list with global ids."""
    nodes, gid = [], 0
    rec_n = rec_d = 0
    for t in frames:
        b = json.load(open(os.path.join(d, f"base85_t{t}.json")))["nodes"]
        s85 = json.load(open(os.path.join(d, f"sm85_t{t}.json")))["nodes"]
        s80 = json.load(open(os.path.join(d, f"sm80_t{t}.json")))["nodes"]
        if cfg == "A": use = b
        elif cfg == "B": use = s85
        elif cfg == "C": use = s80
        elif cfg == "D": use = fuse(b, s85)
        elif cfg == "E": use = fuse(b, s80)
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        _, g2p = match_nodes(use, g)
        rec_n += len(g2p); rec_d += len(g)
        for n in use:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    return nodes, rec_n / rec_d

res = {}
for cfg in ("A", "B", "C", "D", "E"):
    nodes, rec = build(cfg)
    pred = BL.link({"nodes": nodes, "edges": []})
    assert pred.get("phased") is not True, "no split flags expected here"
    agg = score_samples([(cfg, pred, gsub, None)])
    s = agg["per_sample"][0]
    res[cfg] = {"recall": rec, "n_det": len(nodes),
                "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
                "ec": s["edge_counts"]}
    print(f"  {cfg}: rec={rec:.3f} det={len(nodes)} raw={s['edge_jaccard_raw']:.4f} "
          f"adj={s['adjusted_edge_jaccard']:.4f} ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
# determinism check: A must equal EXP-0013 A exactly
ref13 = json.load(open(os.path.join(d, "..", "EXP-0013", "metrics.json")))["configs"]["A"]
det_ok = (abs(res["A"]["recall"] - 0.982 - 0.0) < 0.002 and
          abs(res["A"]["raw"] - ref13["raw"]) < 1e-9 and res["A"]["ec"] == ref13["ec"])
print("  determinism A==EXP-0013A:", det_ok, ref13["ec"], res["A"]["ec"])
base = res["A"]
cands = {c: res[c] for c in ("B", "C", "D", "E")}
go = {c: (v["recall"] >= base["recall"] - 1e-12 and v["raw"] >= base["raw"] - 1e-12
          and v["adj"] >= base["adj"] - 1e-12) for c, v in cands.items()}
metrics = {"exp_id": "EXP-0014", "title": "Dim-cell small-sigma fused detection",
           "hypothesis_id": "H-002", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "blocks": frames, "configs": res, "determinism_A_reproduced": bool(det_ok),
           "go_full_video": go,
           "decision": "keep-trying",
           "decision_reason": ("Window verdict per config; GO configs -> EXP-0015 full-video. "
                               "Ceiling keep-trying (window rung).")}
assert det_ok, "NONDETERMINISM: A != EXP-0013 A"
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("GO:", go)
if not any(go.values()): print("STOP (recorded): scale fusion does not pay")
EOF
echo "[EXP-0014] OK: metrics.json written."
