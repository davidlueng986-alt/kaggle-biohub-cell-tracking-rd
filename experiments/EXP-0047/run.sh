#!/usr/bin/env bash
# EXP-0047: gate-10 vs gate-7 on DARK image graphs (linking-only, cheap).
# Reassembles frozen EXP-0021 detection nodes, re-links with BL.link maxd 7 vs 10,
# scores vs GT. Tests whether v7 gate-7 choice holds on dark samples (hidden relevance).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0047"
SRC="$ROOT/experiments/EXP-0021"
python3 - "$EXP" "$SRC" "$ROOT" <<'EOF'
import json, os, sys
exp, src, root = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
from score import score_samples
SIDS = ["44b6_0b24845f", "44b6_0c582fdc", "6bba_05db0fb1", "6bba_062c8d37", "6bba_05b6850b"]
rows = {}
for sid in SIDS:
    gt = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    nodes, gid = [], 0
    for t in range(100):
        det = json.load(open(os.path.join(src, f"full_{sid}_t{t}.json")))
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    out = {}
    for tag, maxd in [("g7", 7.0), ("g10", 10.0)]:
        pred = BL.link({"nodes": [dict(n) for n in nodes], "edges": []}, maxd=maxd)
        agg = score_samples([(sid, pred, gt, None)])
        s = agg["per_sample"][0]
        ec, dc = s["edge_counts"], s["division_counts"]
        out[tag] = {"raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
                    "ec": [ec["TP"], ec["FP"], ec["FN"]],
                    "div": [dc["TP"], dc["FP"], dc["FN"]], "score": s["score"]}
        print(f"  {sid} {tag}: raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
              f"ec={ec['TP']}/{ec['FP']}/{ec['FN']}", flush=True)
    out["delta_adj_g10_g7"] = out["g10"]["adj"] - out["g7"]["adj"]
    rows[sid] = out
json.dump(rows, open(os.path.join(exp, "metrics.json"), "w"), indent=2)
# verdict: gate-7 holds if g10-g7 <= 0 on >=3/5 (image side rejects widening, cf EXP-0017 arm2)
holds = sum(1 for s in rows if rows[s]["delta_adj_g10_g7"] <= 0)
verdict = "HOLD-g7" if holds >= 3 else "CHALLENGE-g7"
print(f"VERDICT {verdict}: g7-holds on {holds}/5 dark+ref")
json.dump({"verdict": verdict, "holds": holds, "rows": rows},
          open(os.path.join(exp, "verdict.json"), "w"), indent=2)
EOF
echo "[EXP-0047] done -> metrics.json + verdict.json"
