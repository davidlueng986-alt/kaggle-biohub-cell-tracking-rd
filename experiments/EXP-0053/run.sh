#!/usr/bin/env bash
# Runner for EXP-0053 — trusted CV rebaseline (PROTOCOL v1.2).
# Long run (detection gaps dominate). Exits 0; verdict in metrics.json.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0053] trusted rebaseline (full 6-sample LOSO + embryo-nested)..."
python3 "$ROOT/scripts/trusted_cv.py" --full \
  --det-cache "$EXP_DIR/det" --out "$EXP_DIR/raw.json"
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
raw = json.load(open(os.path.join(d, "raw.json")))
metrics = dict(raw)
metrics.update({
    "exp_id": "EXP-0053",
    "title": "Trusted CV rebaseline standing DoG",
    "hypothesis_id": "H-002+H-004",
    "dry_run": False, "real_data": True, "image_based": True,
    "simplified_scorer": False,
    "decision": "keep-trying",
    "decision_reason": ("Rebaseline defines the trusted standing (BTE); "
                        "no promotion content. Compare loso_worst/micro vs "
                        "tuned_ref 0.8194 and public 0.650/0.668 in notes."),
})
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
r = metrics
print(f"loso_micro={r['loso_micro']:.4f} loso_worst={r['loso_worst']:.4f} "
      f"embryo_nested_worst={r['embryo_nested_worst']:.4f} "
      f"({r['elapsed_s']:.0f}s)")
for sid, row in sorted(r["loso_table"].items()):
    print(f"  holdout {sid}: HP=({row['fitted_pct']},{row['fitted_gate']}) "
          f"edge={row['edge']:.4f} score={row['score']:.4f}")
for emb, row in sorted(r["embryo_nested"].items()):
    print(f"  nested holdout {emb}: HP={row['HP']} micro={row['micro']:.4f}")
EOF
echo "[EXP-0053] OK: metrics.json written."
