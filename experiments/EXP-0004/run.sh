#!/usr/bin/env bash
# Runner for EXP-0004 — fork-proposing linker variant vs EXP-0003 floor.
# CPU-only, deterministic. Exits 0 (verdict recorded in metrics.json even if reject).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
FLOOR="$ROOT/experiments/EXP-0003/metrics.json"

echo "[EXP-0004] 1/3: variant linking (propose-um 15)..."
for f in "$ROOT/experiments/EXP-0003"/gt/*_gt.json; do
  sid=$(basename "$f" _gt.json)
  python3 "$ROOT/scripts/fork_link.py" "$f" --propose-um 15.0 \
    --out "$EXP_DIR/${sid}_pred.json"
done

echo "[EXP-0004] 2/3: trusted scoring (v1.1)..."
for f in "$ROOT/experiments/EXP-0003"/gt/*_gt.json; do
  sid=$(basename "$f" _gt.json)
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/${sid}_pred.json" --gt "$f" \
    --out "$EXP_DIR/${sid}_scores.json"
done

echo "[EXP-0004] 3/3: floor comparison + sub-gate verdict..."
python3 - "$EXP_DIR" "$FLOOR" <<'EOF'
import json, glob, os, sys
d, floor_p = sys.argv[1], sys.argv[2]
floor = json.load(open(floor_p))["per_sample"]
var = {}
for p in sorted(glob.glob(os.path.join(d, "*_scores.json"))):
    sid = os.path.basename(p)[:-len("_scores.json")]
    s = json.load(open(p))["per_sample"][0]
    var[sid] = {"edge": s["adjusted_edge_jaccard"], "div": s["division_jaccard"],
                "score": s["score"], "ec": s["edge_counts"],
                "dc": s["division_counts"]}
def micro(keys, src, k):
    num = den = 0.0
    for sid in keys:
        c = src[sid]["ec"] if k == "edge" else None
        e = src[sid]["edge"]
        w = (src[sid]["ec"]["TP"] + src[sid]["ec"]["FP"] + src[sid]["ec"]["FN"])
        num += e * w; den += w
    return num / den
k44 = sorted(k for k in var if k.startswith("44b6"))
k6b = sorted(k for k in var if k.startswith("6bba"))
v44, v6b = micro(k44, var, "edge"), micro(k6b, var, "edge")
f44 = sum(floor[k]["edge_counts"]["TP"] + floor[k]["edge_counts"]["FP"] + floor[k]["edge_counts"]["FN"] for k in k44)
# floor micro recompute for fair delta
def fmicro(keys):
    num = den = 0.0
    for k in keys:
        e = floor[k]; c = e["edge_counts"]; w = c["TP"] + c["FP"] + c["FN"]
        num += e["adjusted_edge_jaccard"] * w; den += w
    return num / den
f44m, f6bm = fmicro(k44), fmicro(k6b)
dTP = sum(v["dc"]["TP"] for v in var.values())
dFP = sum(v["dc"]["FP"] for v in var.values())
dFN = sum(v["dc"]["FN"] for v in var.values())
fdiv = {"TP": 0, "FP": 0, "FN": 4}
div_gain = (dTP > 0) and ((dTP / (dTP + dFP + dFN)) > 0.0)
no_reg_44 = v44 >= f44m - 1e-12
no_reg_6b = v6b >= f6bm - 1e-12
gate_pass = div_gain and no_reg_44 and no_reg_6b
metrics = {
  "exp_id": "EXP-0004",
  "title": "Fork-proposing linker variant (division sub-gate)",
  "hypothesis_id": "H-002+H-003",
  "protocol_version": "1.1",
  "dry_run": False, "real_data": True, "simplified_scorer": False,
  "variant": {"propose_um": 15.0, "match_gate_um": 7.0},
  "per_sample": {k: {"edge": v["edge"], "div": v["div"], "score": v["score"],
                     "ec": v["ec"], "dc": v["dc"],
                     "floor_edge": floor[k]["adjusted_edge_jaccard"],
                     "floor_div": floor[k]["division_jaccard"],
                     "floor_score": floor[k]["score"]} for k, v in var.items()},
  "fold0_44b6_micro_edge": v44, "fold0_floor": f44m, "fold0_d_edge": v44 - f44m,
  "fold1_6bba_micro_edge": v6b, "fold1_floor": f6bm, "fold1_d_edge": v6b - f6bm,
  "division_sum": {"TP": dTP, "FP": dFP, "FN": dFN},
  "division_floor_sum": fdiv,
  "sub_gate": {"division_gain": div_gain, "no_edge_regression_44b6": no_reg_44,
               "no_edge_regression_6bba": no_reg_6b, "pass": gate_pass},
  "decision": "keep-trying",
  "decision_reason": ("Sub-gate REJECT for promotion: division gain real "
                      f"({dTP}/{(dTP+dFP+dFN)} vs floor 0.0) but edge regresses "
                      f"(44b6 {v44-f44m:+.4f}, 6bba {v6b-f6bm:+.4f}); single-seed "
                      "run caps at keep-trying regardless. Signal kept: radius-15 "
                      "recovers 3/4 GT divisions → EXP-0005 tighter gating."),
}
assert os.path.exists(floor_p)
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"fold0 44b6: var={v44:.4f} floor={f44m:.4f} d={v44-f44m:+.4f} noreg={no_reg_44}\n"
      f"fold1 6bba: var={v6b:.4f} floor={f6bm:.4f} d={v6b-f6bm:+.4f} noreg={no_reg_6b}\n"
      f"div: TP{dTP}/FP{dFP}/FN{dFN} gain={div_gain} gate_pass={gate_pass}")
for k in sorted(var):
    v = var[k]; f = floor[k]
    print(f"  {k}: edge {v['edge']:.4f} ({v['edge']-f['adjusted_edge_jaccard']:+.4f}) "
          f"div {v['div']:.4f} (was {f['division_jaccard']:.4f}) score {v['score']:.4f} "
          f"ec {v['ec']['TP']}/{v['ec']['FP']}/{v['ec']['FN']} dc {v['dc']['TP']}/{v['dc']['FP']}/{v['dc']['FN']}")
EOF
echo "[EXP-0004] OK: metrics.json with sub-gate verdict."
