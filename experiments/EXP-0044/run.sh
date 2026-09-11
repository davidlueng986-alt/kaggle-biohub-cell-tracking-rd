#!/usr/bin/env bash
# Runner for EXP-0044 — image r10 forks on 6bba_05db0fb1 full video (3 GT divs).
# Frozen-artifact reuse only: per-frame @98.5 detections from EXP-0021
# (mission text said EXP-0009, but EXP-0009 only holds 44b6_0113de3b +
# 6bba_05b6850b; the 6bba_05db0fb1 @98.5 per-frame dets live in EXP-0021 —
# same pct, verified above; byte-reuse, no re-detection here).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05db0fb1"
DET_DIR="$ROOT/experiments/EXP-0021"
GT="$ROOT/experiments/EXP-0003/gt/${SID}_gt.json"

echo "[EXP-0044] 1/3: assemble full-video nodes (global re-id) + link..."
python3 - "$EXP_DIR" "$ROOT" "$DET_DIR" <<'EOF'
import json, os, sys
exp_dir, root, det_dir = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
import fork_link as FL
sid = "6bba_05db0fb1"
nodes, gid = [], 0
for t in range(100):
    det = json.load(open(os.path.join(det_dir, f"full_{sid}_t{t}.json")))
    assert det["nodes"], f"empty det file t={t}"
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
graph = {"nodes": nodes, "edges": []}
base = BL.link(graph)  # gate-7 default (MAXD=7.0)
json.dump(base, open(os.path.join(exp_dir, "base_pred.json"), "w"))
print(f"  base: nodes={len(nodes)} edges={len(base['edges'])} assign={base.get('assign')}")
fork = FL.link(graph, propose_um=10.0)  # r10 on gate-7 base; base_maxd default
json.dump(fork, open(os.path.join(exp_dir, "fork_r10_pred.json"), "w"))
print(f"  fork_r10: edges={len(fork['edges'])} fork_extra={fork['n_fork_extra']} base_maxd={fork['base_maxd']}")
EOF

echo "[EXP-0044] 2/3: score base + fork vs full GT (true T_true)..."
python3 "$ROOT/scripts/score.py" \
  --pred "$EXP_DIR/base_pred.json" --gt "$GT" \
  --out "$EXP_DIR/base_scores.json" > "$EXP_DIR/base_score_stdout.txt"
python3 "$ROOT/scripts/score.py" \
  --pred "$EXP_DIR/fork_r10_pred.json" --gt "$GT" \
  --out "$EXP_DIR/fork_r10_scores.json" > "$EXP_DIR/fork_score_stdout.txt"

echo "[EXP-0044] 3/3: base-vs-fork table + verdict -> metrics.json..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
base = json.load(open(os.path.join(d, "base_scores.json")))["per_sample"][0]
fork = json.load(open(os.path.join(d, "fork_r10_scores.json")))["per_sample"][0]
def row(s):
    return {"recall": None, "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
            "TP": s["edge_counts"]["TP"], "FP": s["edge_counts"]["FP"], "FN": s["edge_counts"]["FN"],
            "div_TP": s["division_counts"]["TP"], "div_FP": s["division_counts"]["FP"],
            "div_FN": s["division_counts"]["FN"], "div_j": s["division_jaccard"],
            "score": s["score"], "T_pred": s["T_pred"], "T_true": s["T_true"]}
b, f = row(base), row(fork)
d_adj = f["adj"] - b["adj"]
d_div_tp = f["div_TP"] - b["div_TP"]
d_div_fp = f["div_FP"] - b["div_FP"]
# Verdict: GO if div TP>=1 with div FP==0 AND edge adj >= base;
# MIXED if div gain with small edge cost; STOP if div FP>0 w/o TP gain or edge regresses >0.01.
if f["div_TP"] >= 1 and f["div_FP"] == 0 and f["adj"] >= b["adj"]:
    verdict = "GO"
elif d_div_tp > 0 and d_adj >= -0.01:
    verdict = "MIXED"
elif (f["div_FP"] > 0 and d_div_tp <= 0) or d_adj < -0.01:
    verdict = "STOP"
elif d_div_tp > 0:
    verdict = "MIXED"
else:
    verdict = "STOP"
m = {"exp_id": "EXP-0044", "title": "Image r10 forks on 6bba_05db0fb1 full video (3 GT divisions)",
     "status": "done", "protocol_version": "1.1", "scorer_version": "1.1.0",
     "det_source": "experiments/EXP-0021/full_6bba_05db0fb1_t<0-99>.json @98.5 (mission text said EXP-0009; files live in EXP-0021)",
     "gt": "experiments/EXP-0003/gt/6bba_05db0fb1_gt.json",
     "base": b, "fork_r10": f,
     "delta": {"d_adj": d_adj, "d_raw": f["raw"] - b["raw"], "d_div_TP": d_div_tp,
               "d_div_FP": d_div_fp, "d_score": f["score"] - b["score"]},
     "verdict": verdict}
json.dump(m, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(json.dumps({"base": b, "fork": f, "delta": m["delta"], "verdict": verdict}, indent=2))
EOF
echo "[EXP-0044] done. verdict in metrics.json"
