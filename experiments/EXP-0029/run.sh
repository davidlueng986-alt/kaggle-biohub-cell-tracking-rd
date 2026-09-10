#!/usr/bin/env bash
# Runner for EXP-0029 — truncate gate (kernel upgrade decided from verdict).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0029] 1/2: window detects @truncate 2.0..."
for t in 20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/6bba_05b6850b.zarr" \
    --t "$t" --pct 98.5 --truncate 2.0 --out "$EXP_DIR/T2_t${t}.json" > /dev/null
done
echo "  detection done"

echo "[EXP-0029] 2/2: fidelity + edge + timing verdict..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
frames = list(range(20, 30)) + list(range(40, 50))
gt_full = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in frames}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in frames],
        "edges": [e for e in gt_full["edges"] if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(frames) / 100)}
mm = 0
t_new = t_old = 0.0
for t in frames:
    a = json.load(open(os.path.join(d, f"T2_t{t}.json")))
    b = json.load(open(os.path.join(root, "experiments/EXP-0013", f"A_t{t}.json")))
    sa = sorted([(n["z"], n["y"], n["x"]) for n in a["nodes"]])
    sb = sorted([(n["z"], n["y"], n["x"]) for n in b["nodes"]])
    if sa != sb:
        mm += 1
    t_new += a["params"]["elapsed_s"]
# old timing from frozen files
for t in frames:
    b = json.load(open(os.path.join(root, "experiments/EXP-0013", f"A_t{t}.json")))
    t_old += b["params"]["elapsed_s"]
print(f"  mismatched frames: {mm}/20, t_new={t_new:.1f}s t_old={t_old:.1f}s")
nodes, gid, rec_n, rec_d = [], 0, 0, 0
for t in frames:
    for n in json.load(open(os.path.join(d, f"T2_t{t}.json")))["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    g = [n for n in gt_full["nodes"] if n["t"] == t]
    det = json.load(open(os.path.join(d, f"T2_t{t}.json")))["nodes"]
    _, g2p = match_nodes(det, g)
    rec_n += len(g2p); rec_d += len(g)
pred = BL.link({"nodes": nodes, "edges": []})
s = score_samples([("T2", pred, gsub, None)])["per_sample"][0]
print(f"  T2: rec={rec_n/rec_d:.3f} raw={s['edge_jaccard_raw']:.4f} ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
speedup = round(t_old / t_new, 2) if t_new else 0.0
adopt = (mm == 0 and s["edge_counts"] == {"TP": 143, "FP": 2, "FN": 5} and speedup >= 1.1)
metrics = {"exp_id": "EXP-0029", "title": "Truncated gaussians + kernel upgrade prep",
           "hypothesis_id": "H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "mismatched_frames": mm,
           "edge": {"raw": s["edge_jaccard_raw"], "ec": s["edge_counts"]},
           "timing": {"old_s": round(t_old, 1), "new_s": round(t_new, 1), "speedup": speedup},
           "truncate_adopted_as_option": bool(adopt),
           "decision": "keep-trying",
           "decision_reason": ("Truncate-2.0 " + ("ADOPTED as validated option (kernel passes it explicitly; default stays 4.0). " if adopt else "REJECTED (artifacts matter) — stay at 4.0. ") + "Kernel upgrade next with adopted opts.")}
assert True  # ledger records either verdict
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("adopt-as-option:", adopt)
EOF
echo "[EXP-0029] OK: metrics.json written."
