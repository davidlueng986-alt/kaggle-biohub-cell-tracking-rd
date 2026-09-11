#!/usr/bin/env bash
# Runner for EXP-0050 — gate-7 vs gate-10 linker gate test, all 6 IMAGE graphs.
# CPU-only, deterministic. Links FROZEN detections only (no re-detection),
# scores both gates vs full GT (true T_true) with trusted scorer v1.1.0.
# Exits 0 (verdict lives in metrics.json even if MIXED).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0050] link both gates + score all 6 (frozen det reuse)..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
from score import score_single

# frozen det source per sample (percentile frozen at collection time)
SRC = {
    "44b6_0113de3b": "experiments/EXP-0008",  # @99.0
    "6bba_05b6850b": "experiments/EXP-0009",  # @98.5
    "44b6_0b24845f": "experiments/EXP-0021",  # @99.0
    "44b6_0c582fdc": "experiments/EXP-0021",  # @99.0
    "6bba_05db0fb1": "experiments/EXP-0021",  # @98.5
    "6bba_062c8d37": "experiments/EXP-0021",  # @98.5
}
SIDS = list(SRC)
per_sample = {}
for sid in SIDS:
    sdir = os.path.join(root, SRC[sid])
    gt = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    # assemble full video; det ids restart per frame -> reassign globally unique gid
    # (keep id/t/z/y/x only, matching EXP-0021 reference behavior)
    nodes, gid = [], 0
    for t in range(100):
        det = json.load(open(os.path.join(sdir, f"full_{sid}_t{t}.json")))
        assert det["nodes"], f"empty det frame {sid} t={t}"
        for n in det["nodes"]:
            gid += 1
            assert n["t"] == t, f"frame mismatch {sid} t={t}"
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    T_pred = gid
    row = {"T_pred": T_pred, "T_true": gt.get("T_true"), "src": SRC[sid].split("/")[-1]}
    for gate, key in ((7.0, "gate7"), (10.0, "gate10")):
        pred = BL.link({"nodes": nodes, "edges": []}, maxd=gate)
        json.dump(pred, open(os.path.join(d, f"{sid}_pred_g{int(gate)}.json"), "w"))
        s = score_single(pred, gt)
        row[key] = {
            "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
            "div": s["division_jaccard"], "score": s["score"],
            "ec": s["edge_counts"], "dc": s["division_counts"],
            "assign": pred.get("assign"),
        }
        e = s["edge_counts"]
        print(f"  {sid} g{int(gate):2d}: raw={s['edge_jaccard_raw']:.4f} "
              f"adj={s['adjusted_edge_jaccard']:.6f} div={s['division_jaccard']:.3f} "
              f"TP/FP/FN={e['TP']}/{e['FP']}/{e['FN']} "
              f"dc={s['division_counts']['TP']}/{s['division_counts']['FP']}/{s['division_counts']['FN']} "
              f"[{pred.get('assign')}]", flush=True)
    g7, g10 = row["gate7"]["adj"], row["gate10"]["adj"]
    row["delta_adj_g7_minus_g10"] = g7 - g10
    row["winner"] = "gate7" if g7 >= g10 else "gate10"
    per_sample[sid] = row

flips = sorted([s for s, r in per_sample.items() if r["winner"] == "gate10"])
verdict = "CONFIRM" if not flips else "MIXED"
out = {"exp_id": "EXP-0050",
       "title": "Gate-7 vs gate-10 linker gate test, all 6 IMAGE graphs",
       "protocol_version": "1.1", "scorer_version": "1.1.0",
       "linker": "baseline_link.link", "image_based": True, "real_data": True,
       "per_sample": per_sample, "flips": flips, "verdict": verdict}
json.dump(out, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0050] verdict={verdict} flips={flips}")
EOF
echo "[EXP-0050] done. see metrics.json"
