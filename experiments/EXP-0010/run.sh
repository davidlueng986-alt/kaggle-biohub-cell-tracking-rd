#!/usr/bin/env bash
# Runner for EXP-0010 — per-embryo combo + @98.0 window probe.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0010] 1/2: window probe 6bba t0-9 @98.0..."
for t in 0 1 2 3 4 5 6 7 8 9; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/6bba_05b6850b.zarr" \
    --t "$t" --pct 98.0 --out "$EXP_DIR/probe_t${t}.json" > /dev/null
done

echo "[EXP-0010] 2/2: combo assembly + verdict..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
# --- window probe recall @98.0
gt = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
rs, cs = [], []
for t in range(10):
    det = json.load(open(os.path.join(d, f"probe_t{t}.json")))
    g = [n for n in gt["nodes"] if n["t"] == t]
    _, g2p = match_nodes(det["nodes"], g)
    rs.append(len(g2p) / len(g)); cs.append(len(det["nodes"]))
probe = {"recall_mean": sum(rs) / len(rs),
         "det_per_frame": sum(cs) / len(cs)}
print(f"  window @98.0: recall={probe['recall_mean']:.3f} det/f={probe['det_per_frame']:.0f}")
# --- combo: re-score frozen arms for ledger cleanliness
arms = {"44b6_0113de3b": ("../EXP-0008", "full_44b6_0113de3b_pred.json"),
        "6bba_05b6850b": ("../EXP-0009", "full_6bba_05b6850b_pred.json")}
combo = {}
for sid, (exp, pred) in arms.items():
    g = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    p = json.load(open(os.path.join(d, exp, pred)))
    agg = score_samples([(sid, p, g, None)])
    s = agg["per_sample"][0]
    combo[sid] = {"edge_raw": s["edge_jaccard_raw"], "edge_adj": s["adjusted_edge_jaccard"],
                  "div": s["division_jaccard"], "score": s["score"],
                  "ec": s["edge_counts"], "T_true": s["T_true"]}
    print(f"  combo {sid}: raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f}")
# --- uniform references (recomputed verbatim from ledger rows)
u99 = {"44b6_0113de3b": (0.9038, 0.9382), "6bba_05b6850b": (0.6922, 0.7121)}
u985 = {"44b6_0113de3b": (0.9038, 0.9281), "6bba_05b6850b": (0.7989, 0.8194)}
def worst(pick):
    return min(pick["44b6_0113de3b"][1], pick["6bba_05b6850b"][1])
cworst = min(combo["44b6_0113de3b"]["edge_adj"], combo["6bba_05b6850b"]["edge_adj"])
checks = {
  "combo_ge_u99_per_sample": all(combo[s]["edge_adj"] >= u99[s][1] - 1e-12 for s in combo),
  "combo_ge_u985_per_sample": all(combo[s]["edge_adj"] >= u985[s][1] - 1e-12 for s in combo),
  "combo_ge_u99_worst": cworst >= worst(u99) - 1e-12,
  "combo_ge_u985_worst": cworst >= worst(u985) - 1e-12,
  "probe98_recall_1.00": abs(probe["recall_mean"] - 1.0) < 1e-9,
}
metrics = {"exp_id": "EXP-0010", "title": "Per-embryo combo + @98.0 window probe",
           "hypothesis_id": "H-002", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "combo": combo, "combo_worst": cworst,
           "uniform99_worst": worst(u99), "uniform985_worst": worst(u985),
           "window_probe98": probe,
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Combo/policy verdict per checks. Window probe gates EXP-0011 full-video @98.0. "
                               "Assembly+probe rung: keep-trying ceiling (single deterministic pass).")}
assert True  # ledger records falsified runs too; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0010] OK: metrics.json written."
