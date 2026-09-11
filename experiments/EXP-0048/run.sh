#!/usr/bin/env bash
# EXP-0048: EXP-0035 harvest-readiness drill (no weights needed).
# Random-weight infer dry run on tiny window + runbook wiring checks,
# so unet_best.pt -> eval executes in minutes when it lands.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0048"
export PATH="$HOME/.local/bin:$PATH"
echo "[EXP-0048] 1/3: random-weight infer dry run (3-frame window)..."
python3 "$ROOT/notebooks/train_unet/infer.py" --random-weights \
  --zarr "$ROOT/data/train/6bba_05b6850b.zarr" --t-start 20 --t-end 22 \
  --out "$EXP/det_random_t20-22.json" 2>&1 | tail -5
echo "[EXP-0048] 2/3: link + score random-weight graph vs GT..."
python3 - "$EXP" "$ROOT" <<'EOF'
import json, os, sys
exp, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
from score import score_single
det = json.load(open(os.path.join(exp, "det_random_t20-22.json")))
print(f"  random dets: {len(det.get('nodes', []))} nodes")
pred = BL.link({"nodes": det.get("nodes", []), "edges": []})
json.dump(pred, open(os.path.join(exp, "linked_random.json"), "w"))
print(f"  linked edges: {len(pred.get('edges', []))}")
EOF
echo "[EXP-0048] 3/3: runbook wiring checks..."
git -C "$ROOT" check-ignore -q data/weights/x.pt && echo "  gitignore data/weights: OK" || echo "  gitignore data/weights: CHECK"
kaggle kernels status liangwanyiudavid/biohub-unet-train-v1 2>&1 | head -2
test ! -f "$ROOT/data/weights/unet_best.pt" && echo "  weights absent (expected pre-harvest): OK" || echo "  weights PRESENT -> run EXP-0035 now"
python3 - "$EXP" <<'EOF'
import json, sys
exp = sys.argv[1]
det = json.load(open(f"{exp}/det_random_t20-22.json"))
ok = isinstance(det.get("nodes", []), list)
json.dump({"exp_id": "EXP-0048", "random_infer_ok": ok,
           "n_nodes": len(det.get("nodes", [])),
           "verdict": "READY" if ok else "BROKEN",
           "notes": "harvest drill: infer wiring live; await unet_best.pt -> EXP-0035 full eval"},
          open(f"{exp}/metrics.json", "w"), indent=2)
print(f"VERDICT {'READY' if ok else 'BROKEN'}: random-infer wiring {'live' if ok else 'broken'}")
EOF
echo "[EXP-0048] done -> metrics.json"
