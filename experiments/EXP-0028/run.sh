#!/usr/bin/env bash
# Runner for EXP-0028 — vectorized-centroid fidelity gate.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0028] 1/2: detect windows with new code..."
for t in 20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/6bba_05b6850b.zarr" \
    --t "$t" --pct 98.5 --out "$EXP_DIR/new6b_t${t}.json" > /dev/null
done
for t in 20 21 22 23 24 25 26 27 28 29; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/44b6_0113de3b.zarr" \
    --t "$t" --pct 99.0 --out "$EXP_DIR/new44_t${t}.json" > /dev/null
done
echo "  detection done"

echo "[EXP-0028] 2/2: fidelity + edge + timing verdict..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
frames6 = list(range(20, 30)) + list(range(40, 50))
frames4 = list(range(20, 30))
def pos(nodes):
    return sorted([(n["z"], n["y"], n["x"]) for n in nodes])
mm = tot_new = tot_old = 0
for t in frames6:
    a = json.load(open(os.path.join(d, f"new6b_t{t}.json")))
    b = json.load(open(os.path.join(root, "experiments/EXP-0013", f"A_t{t}.json")))
    if pos(a["nodes"]) != pos(b["nodes"]):
        mm += 1
    tot_new += a["params"]["elapsed_s"]; tot_old += b["params"]["elapsed_s"]
for t in frames4:
    a = json.load(open(os.path.join(d, f"new44_t{t}.json")))
    b = json.load(open(os.path.join(root, "experiments/EXP-0008", f"full_44b6_0113de3b_t{t}.json")))
    if pos(a["nodes"]) != pos(b["nodes"]):
        mm += 1
    tot_new += a["params"]["elapsed_s"]; tot_old += b["params"]["elapsed_s"]
print(f"  mismatched frames: {mm}/30")
# linked edge parity on 6bba window (expect 143/2/5)
gt_full = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in frames6}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in frames6],
        "edges": [e for e in gt_full["edges"] if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(frames6) / 100)}
nodes, gid = [], 0
for t in frames6:
    for n in json.load(open(os.path.join(d, f"new6b_t{t}.json")))["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
pred = BL.link({"nodes": nodes, "edges": []})
s = score_samples([("vec", pred, gsub, None)])["per_sample"][0]
print(f"  linked: raw={s['edge_jaccard_raw']:.4f} ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} (expect 143/2/5)")
checks = {"fidelity_30frames": mm == 0,
          "edge_parity": s["edge_counts"] == {"TP": 143, "FP": 2, "FN": 5}}
speedup = round(tot_old / tot_new, 2) if tot_new else 0.0
metrics = {"exp_id": "EXP-0028", "title": "Vectorized centroids",
           "hypothesis_id": "H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "mismatched_frames": mm,
           "window_edge": {"raw": s["edge_jaccard_raw"], "ec": s["edge_counts"]},
           "timing": {"old_s": round(tot_old, 1), "new_s": round(tot_new, 1), "speedup": speedup},
           "checks": checks, "all_checks_pass": all(checks.values()),
           "adopted": bool(all(checks.values())),
           "decision": "keep-trying",
           "decision_reason": ("Vectorized centroids " + ("ADOPTED (fidelity exact, %.1fx). " % speedup if all(checks.values()) else "REVERTED (fidelity breach) — code reverted in follow-up. ") + "Infra rung: no metric movement by design.")}
assert True  # ledger records either verdict
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks, "speedup:", speedup)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0028] OK: metrics.json written."
