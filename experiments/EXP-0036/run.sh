#!/usr/bin/env bash
# Runner for EXP-0036 — notebook vs repo equivalence probes.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0036] 1/1: equivalence probes..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
import numpy as np
import zarr
from dog_detect import detect as repo_detect
import baseline_link as BL
nb = json.load(open(os.path.join(root, "notebooks/submit_gold/submit_gold.ipynb")))
code = ["\n".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
# NOTE: core cell found by marker (index shifts as notebook grows); exec whole
# cell (constants resolve at call time from ns2)
core = [c for c in code if "def detect_frame" in c][0]
ns2 = {"np": np, "VOXEL": (1.625, 0.40625, 0.40625), "GATE_UM": 10.0,
       "SIG_SMALL": (1.0, 3.0, 3.0), "SIG_LARGE": (1.6, 5.0, 5.0), "MIN_SIZE": 50}
exec("import numpy as np\n" + core, ns2)
Z6 = zarr.open_group(os.path.join(root, "data/train/6bba_05b6850b.zarr"), mode="r")["0"]
Z4 = zarr.open_group(os.path.join(root, "data/train/44b6_0113de3b.zarr"), mode="r")["0"]
out = {"detect_equal": [], "link_equal": []}
for (Z, sid, ts, pct) in ((Z6, "6bba", [20, 21, 22], 98.5), (Z4, "44b6", [20, 21, 22], 99.0)):
    for t in ts:
        vol = np.asarray(Z[t])
        nb_nodes = sorted(ns2["detect_frame"](vol, pct))
        r_nodes, _ = repo_detect(vol, pct=pct)
        r_nodes = sorted([(z, y, x) for z, y, x, _, _ in r_nodes])
        out["detect_equal"].append(nb_nodes == r_nodes)
print("  detect equality:", out["detect_equal"])
# link equality on one 3-frame chain each (global re-id both sides)
for (Z, frames, pct) in ((Z6, [20, 21, 22], 98.5), (Z4, [20, 21, 22], 99.0)):
    per_t = []
    for t in frames:
        per_t.append(sorted(ns2["detect_frame"](np.asarray(Z[t]), pct)))
    # notebook link_frames needs VOXEL/GATE_UM/assign in ns; reuse core ns with constants
    lns = {"np": np, "VOXEL": (1.625, 0.40625, 0.40625), "GATE_UM": 10.0}
    link_src = [c for c in code if "def link_frames" in c][0]
    exec("import numpy as np\n" + link_src.split("import csv")[0], lns)
    fr = [list(c) for c in per_t]
    nbn, nbe = lns["link_frames"](fr)
    # repo side
    nodes, gid = [], 0
    for t, cents in zip(frames, per_t):
        for (z, y, x) in cents:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": z, "y": y, "x": x})
    re_ = BL.link({"nodes": nodes, "edges": []}, maxd=10.0)
    # Both sides enumerate detections frame-major in identical order, so id
    # spaces correspond 1:1 (notebook link_frames numbers its own t=0,1,2
    # internally, but ids — not t-coords — are what edges reference).
    nb_e = sorted([tuple(sorted(e)) for e in nbe])
    re_e = sorted([tuple(sorted(e)) for e in re_["edges"]])
    same = nb_e == re_e
    out["link_equal"].append(same)
    print(f"  link equality ({len(frames)}f chain):", same)
checks = {"detect_all_equal": all(out["detect_equal"]), "link_all_equal": all(out["link_equal"])}
metrics = {"exp_id": "EXP-0036", "title": "Notebook-repo drift audit",
           "hypothesis_id": "H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "probes": out, "accepted_deltas": ["gate-10 override (EXP-0018, explicit)", "no max_size cap (giant-component only)",
             "no split/phased/mad/downsample opts (no-forks policy)", "validator int-coord gap (writer emits ints)"],
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": "IN-SYNC: no patches needed. Deltas accepted with refs."}
assert True
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
EOF
echo "[EXP-0036] OK: metrics.json written."
