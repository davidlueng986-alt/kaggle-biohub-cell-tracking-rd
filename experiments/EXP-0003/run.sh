#!/usr/bin/env bash
# Runner for EXP-0003 — real-data oracle-linker baseline (subset 6).
# CPU-only, deterministic. Exits 0 on success, non-zero on falsification.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0003] 1/4: GT graphs from .geff..."
python3 "$ROOT/scripts/geff_to_graph.py" --all "$ROOT/data/train" \
  --out-dir "$EXP_DIR/gt"

echo "[EXP-0003] 2/4: oracle causal linking..."
for f in "$EXP_DIR"/gt/*_gt.json; do
  sid=$(basename "$f" _gt.json)
  python3 "$ROOT/scripts/baseline_link.py" "$f" \
    --out "$EXP_DIR/${sid}_pred.json"
done

echo "[EXP-0003] 3/4: trusted scoring (v1.1) per sample..."
for f in "$EXP_DIR"/gt/*_gt.json; do
  sid=$(basename "$f" _gt.json)
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/${sid}_pred.json" --gt "$f" \
    --out "$EXP_DIR/${sid}_scores.json"
done

echo "[EXP-0003] 4/4: merge + asserts..."
python3 - "$EXP_DIR" <<'EOF'
import json, glob, os, sys
d = sys.argv[1]
samples = {}
for p in sorted(glob.glob(os.path.join(d, "*_scores.json"))):
    sid = os.path.basename(p)[:-len("_scores.json")]
    agg = json.load(open(p))
    s = agg["per_sample"][0]
    samples[sid] = {"agg": agg, "edge": s["adjusted_edge_jaccard"],
                    "div": s["division_jaccard"], "score": s["score"],
                    "ec": s["edge_counts"], "dc": s["division_counts"],
                    "T_true": s["T_true"]}
assert len(samples) == 6, f"expected 6 scored samples, got {len(samples)}"
assert all(v["T_true"] for v in samples.values()), "T_true missing -> non-promotable"
assert all(v["ec"]["TP"] + v["ec"]["FP"] + v["ec"]["FN"] > 0 for v in samples.values()), "zero-weight sample"
# linker invariant: zero predicted forks -> division FP must be 0
assert all(v["dc"]["FP"] == 0 for v in samples.values()), "linker emitted an evaluable fork?"
e44 = [v for k, v in samples.items() if k.startswith("44b6")]
e6b = [v for k, v in samples.items() if k.startswith("6bba")]
def micro(ws, key):
    num = den = 0
    for v in ws:
        c = v["ec"]; w = c["TP"] + c["FP"] + c["FN"]
        num += v["edge"] * w; den += w
    return num / den
agg44, agg6b = micro(e44, "edge"), micro(e6b, "edge")
dTP = sum(v["dc"]["TP"] for v in samples.values())
dFP = sum(v["dc"]["FP"] for v in samples.values())
dFN = sum(v["dc"]["FN"] for v in samples.values())
metrics = {
  "exp_id": "EXP-0003",
  "title": "Real-data oracle-linker baseline (subset 6)",
  "hypothesis_id": "H-001+H-002",
  "protocol_version": "1.1",
  "dry_run": False,
  "real_data": True,
  "simplified_scorer": False,
  "subset_ids": sorted(samples),
  "per_sample": {k: {"adjusted_edge_jaccard": v["edge"],
                     "division_jaccard": v["div"], "score": v["score"],
                     "edge_counts": v["ec"], "division_counts": v["dc"],
                     "T_true": v["T_true"]} for k, v in samples.items()},
  "embryo_44b6_micro_edge": agg44,
  "embryo_6bba_micro_edge": agg6b,
  "worst_fold_edge": min(agg44, agg6b),
  "division_counts_sum": {"TP": dTP, "FP": dFP, "FN": dFN},
  "decision": "keep-trying",
  "decision_reason": ("Oracle-linker floor on real subset (no training, no forks); "
                      "baseline for H-002 linker ladder. NOT promoted (floor by definition)."),
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
rows = "\n".join(f"  {k}: edge={v['edge']:.4f} div={v['div']:.4f} score={v['score']:.4f} "
                  f"TP/FP/FN={v['ec']['TP']}/{v['ec']['FP']}/{v['ec']['FN']} T={v['T_true']}"
                  for k, v in sorted(samples.items()))
print(f"per-sample:\n{rows}\n44b6_micro={agg44:.4f} 6bba_micro={agg6b:.4f} "
      f"worst={min(agg44, agg6b):.4f} div_sum=TP{dTP}/FP{dFP}/FN{dFN}")
EOF

echo "[EXP-0003] OK: metrics.json written from real-data v1.1 scores."
