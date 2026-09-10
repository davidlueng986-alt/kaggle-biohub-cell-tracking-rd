#!/usr/bin/env bash
# Runner for EXP-0015 — appearance separation measurement (no linker changes).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0015] 1/1: label edges + NCC per class..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys, time
import numpy as np
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
import zarr
from appearance import get_patch, ncc, label_edges
t0 = time.time()
pred = json.load(open(os.path.join(d, "..", "EXP-0009", "full_6bba_05b6850b_pred.json")))
gt = json.load(open(os.path.join(d, "..", "EXP-0003", "gt", "6bba_05b6850b_gt.json")))
labels, _ = label_edges(pred["nodes"], pred["edges"], gt["nodes"], gt["edges"])
Z = zarr.open_group(os.path.join(root, "data/train/6bba_05b6850b.zarr"), mode="r")["0"]
cache = {}
def vol(t):
    if t not in cache:
        cache[t] = np.asarray(Z[t])
        if len(cache) > 6:
            cache.pop(next(iter(cache)))
    return cache[t]
P = {n["id"]: n for n in pred["nodes"]}
vals = {"TP": [], "FP": [], "ignored": []}
for i, (u, v) in enumerate(map(tuple, pred["edges"])):
    a, b = P[u], P[v]
    c = ncc(get_patch(vol(a["t"]), a["z"], a["y"], a["x"]),
            get_patch(vol(b["t"]), b["z"], b["y"], b["x"]))
    vals[labels[i]].append(c)
    if (i + 1) % 1000 == 0:
        print(f"  {i+1}/{len(pred['edges'])} edges...", flush=True)
stats = {}
for k, v in vals.items():
    a = np.array(v)
    stats[k] = {"n": len(v), "mean": round(float(a.mean()), 4),
                "p25": round(float(np.percentile(a, 25)), 4),
                "p50": round(float(np.percentile(a, 50)), 4),
                "p75": round(float(np.percentile(a, 75)), 4)}
    print(f"  {k}: n={len(v)} mean={a.mean():.3f} p25/50/75={np.percentile(a,25):.3f}/{np.percentile(a,50):.3f}/{np.percentile(a,75):.3f}")
margin = stats["TP"]["mean"] - stats["FP"]["mean"]
overlap_ok = stats["FP"]["p75"] < stats["TP"]["p25"]
checks = {"margin_ge_0.15": margin >= 0.15, "quartile_separation": bool(overlap_ok)}
metrics = {"exp_id": "EXP-0015", "title": "Appearance-similarity probe",
           "hypothesis_id": "H-003", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "classes": stats, "margin_TP_FP": round(margin, 4),
           "elapsed_s": round(time.time() - t0, 1),
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Measurement rung per checks. GO/park for EXP-0016 appearance-weighted assignment. "
                               "No linker changed; ceiling keep-trying.")}
assert True  # ledger records negative measurements too; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks, "margin:", round(margin, 4))
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0015] OK: metrics.json written."
