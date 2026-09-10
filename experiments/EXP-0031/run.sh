#!/usr/bin/env bash
# Runner for EXP-0031 — Image-side fork proposals (r10 on gate-7 base, detected graphs).
# CPU-only, deterministic. Rebuilds window graphs from frozen EXP-0013 A_t
# detections (global re-id across the 20 frames), links with BL.link (ref A
# recompute) and fork_link.link(propose_um=10.0, gate-7 base), scores both vs
# the GT subgraph with trusted scorer v1.1, applies the sub-gate, writes metrics.json.
# Exits 0 always (verdict recorded in metrics.json even when STOP).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0031] window image-fork test (frozen A_t detections, r10 on gate-7)..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
exp_dir, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
import fork_link as FL

SID = "6bba_05b6850b"
FRAMES = list(range(20, 30)) + list(range(40, 50))

gt_full = json.load(open(os.path.join(
    root, "experiments/EXP-0003/gt", f"{SID}_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in FRAMES}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in FRAMES],
        "edges": [e for e in gt_full["edges"]
                  if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(FRAMES) / 100)}
gt_ch = {}
for u, v in gsub["edges"]:
    gt_ch.setdefault(u, []).append(v)
n_gt_div = sum(1 for v in gt_ch.values() if len(v) >= 2)
print(f"  GT subgraph: {len(gsub['nodes'])} nodes / {len(gsub['edges'])} edges "
      f"T~{gsub['T_true']} divs={n_gt_div}")

# Window graph from frozen A_t detections; det files restart ids per frame,
# so global re-id here (same construction as EXP-0013 reference A).
nodes, gid, rec_n, rec_d = [], 0, 0, 0
for t in FRAMES:
    det = json.load(open(os.path.join(
        root, "experiments/EXP-0013", f"A_t{t}.json")))
    g = [n for n in gt_full["nodes"] if n["t"] == t]
    _, g2p = match_nodes(det["nodes"], g)
    rec_n += len(g2p)
    rec_d += len(g)
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"],
                      "x": n["x"]})
recall = rec_n / rec_d
print(f"  detections: {len(nodes)} nodes, recall={recall:.4f}")

use = [{"id": n["id"], "t": n["t"], "z": n["z"], "y": n["y"], "x": n["x"]}
       for n in nodes]

predA = BL.link({"nodes": use, "edges": []})
sA = score_samples([("A", predA, gsub, None)])["per_sample"][0]
predF = FL.link({"nodes": use, "edges": []}, propose_um=10.0)
assert predF["base_maxd"] == BL.MAXD == 7.0, "base gate must stay 7 (r10-on-gate7 only)"
sF = score_samples([("F", predF, gsub, None)])["per_sample"][0]

for tag, s in (("A", sA), ("F-r10", sF)):
    print(f"  {tag}: rec={recall:.3f} raw={s['edge_jaccard_raw']:.4f} "
          f"adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
          f"dc={s['division_counts']['TP']}/{s['division_counts']['FP']}/{s['division_counts']['FN']}")
print(f"  fork_extra={predF['n_fork_extra']} "
      f"d_raw={sF['edge_jaccard_raw']-sA['edge_jaccard_raw']:+.4f} "
      f"d_adj={sF['adjusted_edge_jaccard']-sA['adjusted_edge_jaccard']:+.4f}")

# Gate (window-only; div TP>0 impossible — 0 GT divs in window):
# PASS = edge raw+adj >= A AND div FP==0 AND recall >= A - 0.005.
REF = {"recall": 0.982, "raw": 0.9533, "adj": 0.9804}
gate_edge = (sF["edge_jaccard_raw"] >= sA["edge_jaccard_raw"] - 1e-12
             and sF["adjusted_edge_jaccard"] >= sA["adjusted_edge_jaccard"] - 1e-12)
gate_div = (sF["division_counts"]["FP"] == 0)
gate_rec = (recall >= REF["recall"] - 0.005)
go = bool(gate_edge and gate_div and gate_rec)

metrics = {
    "exp_id": "EXP-0031",
    "title": "Image-side fork proposals",
    "protocol_version": "1.1",
    "dry_run": False, "real_data": True, "image_based": True,
    "simplified_scorer": False,
    "sample": SID, "frames": FRAMES,
    "propose_um": 10.0, "base_maxd": predF["base_maxd"],
    "gt_window": {"nodes": len(gsub["nodes"]), "edges": len(gsub["edges"]),
                  "T_true": gsub["T_true"], "n_divisions": n_gt_div},
    "reference_A_recompute": {
        "recall": recall, "n_det": len(nodes),
        "raw": sA["edge_jaccard_raw"], "adj": sA["adjusted_edge_jaccard"],
        "ec": sA["edge_counts"], "dc": sA["division_counts"],
        "div_j": sA["division_jaccard"]},
    "fork_r10": {
        "raw": sF["edge_jaccard_raw"], "adj": sF["adjusted_edge_jaccard"],
        "ec": sF["edge_counts"], "dc": sF["division_counts"],
        "div_j": sF["division_jaccard"],
        "n_fork_extra": predF["n_fork_extra"]},
    "delta": {
        "d_raw": sF["edge_jaccard_raw"] - sA["edge_jaccard_raw"],
        "d_adj": sF["adjusted_edge_jaccard"] - sA["adjusted_edge_jaccard"],
        "d_edge_FP": sF["edge_counts"]["FP"] - sA["edge_counts"]["FP"],
        "d_div_FP": sF["division_counts"]["FP"] - sA["division_counts"]["FP"]},
    "gate": {"edge_ge_A": bool(gate_edge), "div_FP_zero": bool(gate_div),
             "recall_ge_A_minus_005": bool(gate_rec)},
    "decision": "GO" if go else "STOP",
    "decision_reason": ("PASS: r10 proposals harmless on detected graphs -> "
                        "GO full-video image-fork test (recommend EXP-0034, not run here)."
                        if go else
                        "FAIL: r10 on detected graphs adds edge FPs + division FPs "
                        "with zero possible TP (0 GT divs in window) -> STOP: image "
                        "forks parked alongside oracle r10 standalone."),
}
json.dump(metrics, open(os.path.join(exp_dir, "metrics.json"), "w"), indent=2)
print(f"[EXP-0031] gate edge={gate_edge} divFP0={gate_div} rec={gate_rec} -> {metrics['decision']}")
EOF
echo "[EXP-0031] OK: metrics.json written."
