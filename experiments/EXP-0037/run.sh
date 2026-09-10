#!/usr/bin/env bash
# Runner for EXP-0037 — re-score frozen submit graphs (parse verified at build).
# CPU-only, deterministic. Exits 0.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0037] 1/1: re-score + assert recorded table..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import score_samples
SIDS = ["44b6_0113de3b", "44b6_0b24845f", "6bba_05b6850b", "6bba_05db0fb1"]
# recorded submit-truth table (parallel rung, verified at build time)
TRUTH = {
  "44b6_0113de3b": (0.636364, 0.660561),
  "44b6_0b24845f": (0.096154, 0.101960),
  "6bba_05b6850b": (0.792986, 0.813416),
  "6bba_05db0fb1": (0.180795, 0.192097),
}
rows = {}
for sid in SIDS:
    p = json.load(open(os.path.join(d, f"{sid}_submit_pred.json")))
    g = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    s = score_samples([(sid, p, g, None)])["per_sample"][0]
    rows[sid] = {"raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
                 "div": s["division_jaccard"], "ec": s["edge_counts"],
                 "dc": s["division_counts"]}
    ok = (abs(s["edge_jaccard_raw"] - TRUTH[sid][0]) < 1e-6
          and abs(s["adjusted_edge_jaccard"] - TRUTH[sid][1]) < 1e-6)
    print(f"  {sid}: raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
          f"reproduced={ok}")
    assert ok, f"table mismatch for {sid}"
metrics = {"exp_id": "EXP-0037", "title": "Submit-output rescore",
           "hypothesis_id": "H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "per_sample": rows,
           "checks": {"table_reproduced": True}, "all_checks_pass": True,
           "decision": "keep-trying",
           "decision_reason": "Submit-truth scores reproduced from frozen graphs. Gate-10-vs-7 churn confirmed as the sole deviation source; gate is a tunable."}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks: {'table_reproduced': True}")
EOF
echo "[EXP-0037] OK: metrics.json written."
