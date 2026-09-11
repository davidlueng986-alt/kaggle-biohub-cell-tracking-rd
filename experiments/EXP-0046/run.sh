#!/usr/bin/env bash
# EXP-0046 runner: base (gate-7) + orphan second-edge pass + score vs full GT (true T_true).
# Deterministic, CPU-only. Writes metrics.json in this dir.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0046"
cd "$ROOT"
for SID in 6bba_062c8d37 6bba_05db0fb1; do
  python3 "$EXP/orphan_pass.py" "$ROOT/experiments/EXP-0021/${SID}_pred.json" \
    --out-pass "$EXP/${SID}_pass.json" \
    --out-base "$EXP/${SID}_base.json" \
    --report "$EXP/${SID}_report.json"
done
python3 - "$EXP" <<'EOF'
import json, sys
sys.path.insert(0, "/home/box/workspace/kaggle-biohub-rd/scripts")
import score as S
exp = sys.argv[1]
rows = {}
for sid in ["6bba_062c8d37", "6bba_05db0fb1"]:
    gt = json.load(open(f"{exp}/../EXP-0003/gt/{sid}_gt.json"))
    # frozen EXP-0021 det preds; base/pass graphs live in exp dir (gid nodes)
    out = {}
    for tag in ["base", "pass"]:
        pred = json.load(open(f"{exp}/{sid}_{tag}.json"))
        s = S.score_single(pred, gt)  # true T_true from GT file
        ec, dc = s["edge_counts"], s["division_counts"]
        rec = ec["TP"] / (ec["TP"] + ec["FN"]) if (ec["TP"] + ec["FN"]) else 1.0
        out[tag] = {
            "edge_TP": ec["TP"], "edge_FP": ec["FP"], "edge_FN": ec["FN"],
            "edge_recall": rec, "edge_raw": s["edge_jaccard_raw"],
            "edge_adj": s["adjusted_edge_jaccard"],
            "div_TP": dc["TP"], "div_FP": dc["FP"], "div_FN": dc["FN"],
            "div_jaccard": s["division_jaccard"], "score": s["score"],
            "T_pred": s["T_pred"], "T_true": s["T_true"],
        }
    rows[sid] = out
# verdict: pre-registered bar
a, b = rows["6bba_062c8d37"], rows["6bba_05db0fb1"]
rep_a = json.load(open(f"{exp}/6bba_062c8d37_report.json"))
rep_b = json.load(open(f"{exp}/6bba_05db0fb1_report.json"))
main_ok = (a["pass"]["div_TP"] >= 1 and a["pass"]["div_FP"] == 0
           and a["pass"]["edge_adj"] >= a["base"]["edge_adj"])
ctrl_ok = (rep_b["n_added"] == 0)
verdict = "GO" if (main_ok and ctrl_ok) else "STOP"
m = {"experiment": "EXP-0046", "protocol_version": "1.1",
     "scorer_version": "1.1.0",
     "method": "orphan-driven second-edge pass (incoming-less w within 10um of v, one extra per source with outdeg==1)",
     "base": "baseline_link gate-7 on gid re-id detections, recomputed in-run",
     "per_sample": rows,
     "reports": {"6bba_062c8d37": rep_a, "6bba_05db0fb1": rep_b},
     "bar": {"main": "062c8d37 div TP>=1, div FP==0, edge adj >= base",
             "control": "05db0fb1 zero new forks"},
     "bar_main_ok": main_ok, "bar_control_ok": ctrl_ok, "verdict": verdict}
json.dump(m, open(f"{exp}/metrics.json", "w"), indent=2)
print(json.dumps(m, indent=2))
print("VERDICT:", verdict)
EOF
