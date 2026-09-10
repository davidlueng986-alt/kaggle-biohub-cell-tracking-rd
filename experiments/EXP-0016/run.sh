#!/usr/bin/env bash
# Runner for EXP-0016 — soft appearance-weighted assignment, window gate.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0016] 1/1: weighted linking grid + verdict..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys, time
import numpy as np
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
import zarr
from appearance import link_weighted
from score import score_samples
t0 = time.time()
frames = list(range(20, 30)) + list(range(40, 50))
Z = zarr.open_group(os.path.join(root, "data/train/6bba_05b6850b.zarr"), mode="r")["0"]
cache = {}
def get_vol(t):
    if t not in cache:
        cache[t] = np.asarray(Z[t])
    return cache[t]
gt_full = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in frames}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in frames],
        "edges": [e for e in gt_full["edges"] if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(frames) / 100)}
# frozen EXP-0013 A detections (no re-detection)
by_t = {}
for t in frames:
    det = json.load(open(os.path.join(d, "..", "EXP-0013", f"A_t{t}.json")))
    by_t[t] = det["nodes"]
res = {}
for W in (0, 1, 2, 4):
    # global re-id: det files restart ids per frame; collisions would forge
    # cross-frame identities (found during debug: 601-FP blowup). Strip flags
    # for the legacy single path (A_t files carry split:false anyway).
    remap, flat, gid = {}, [], 0
    for t in frames:
        for n in by_t[t]:
            gid += 1
            remap[(t, n["id"])] = gid
            flat.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    fbt = {}
    for n in flat:
        fbt.setdefault(n["t"], []).append(n)
    edges, n_ncc = link_weighted(fbt, get_vol, W=W)
    nodes = flat
    agg = score_samples([(f"W{W}", {"nodes": nodes, "edges": edges}, gsub, None)])
    s = agg["per_sample"][0]
    # TP-cost: GT-TP edges held by W=0 but lost here (computed after W0 row)
    res[W] = {"edges": edges, "n_ncc": n_ncc,
              "raw": s["edge_jaccard_raw"], "adj": s["adjusted_edge_jaccard"],
              "ec": s["edge_counts"], "tpcost": None}
    print(f"  W={W}: raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} ncc={n_ncc}", flush=True)
# anchor: W=0 must equal EXP-0013 A exactly
ref13 = json.load(open(os.path.join(d, "..", "EXP-0013", "metrics.json")))["configs"]["A"]
anchor = (res[0]["ec"] == {"TP": 143, "FP": 2, "FN": 5} and abs(res[0]["raw"] - ref13["raw"]) < 1e-12)
print("  anchor W0==EXP-0013A:", anchor)
# TP-cost vs W=0 arm: GT-TP-labeled W0 edges absent from W's set (label_edges
# mirrors score.py exactly; uses flat global-id nodes + GT subgraph)
from appearance import label_edges
all_nodes, _gid = [], 0
for t in frames:
    for n in by_t[t]:
        _gid += 1
        all_nodes.append({"id": _gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
lab0, _ = label_edges(all_nodes, res[0]["edges"], gsub["nodes"], gsub["edges"])
tp0 = {e for i, e in enumerate(map(tuple, res[0]["edges"])) if lab0[i] == "TP"}
for W in (1, 2, 4):
    wset = {tuple(e) for e in res[W]["edges"]}
    res[W]["tpcost"] = sum(1 for e in tp0 if e not in wset)
base = res[0]
go = {}
for W in (1, 2, 4):
    v = res[W]
    go[W] = (v["raw"] >= base["raw"] - 1e-12 and v["adj"] >= base["adj"] - 1e-12
             and v["tpcost"] <= 1)
    print(f"  W={W} vs W0: d_raw={v['raw']-base['raw']:+.4f} d_adj={v['adj']-base['adj']:+.4f} tpcost={v['tpcost']} GO={go[W]}")
for W in res:
    del res[W]["edges"]
metrics = {"exp_id": "EXP-0016", "title": "Soft appearance-weighted assignment",
           "hypothesis_id": "H-003", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "blocks": frames, "W_grid": {str(k): v for k, v in res.items()},
           "anchor_W0_reproduced": bool(anchor),
           "go_full_video": {str(k): bool(v) for k, v in go.items()},
           "elapsed_s": round(time.time() - t0, 1),
           "decision": "keep-trying",
           "decision_reason": ("Window verdict per W; GO Ws -> EXP-0017 full-video. "
                               "Ceiling keep-trying (window rung).")}
assert True  # ledger records negative gates too; verdict in go_full_video
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
assert anchor, "ANCHOR FAILED: W=0 != EXP-0013 A (nondeterminism bug)"
print("GO:", go)
if not any(go.values()): print("STOP (recorded): soft weighting unspendable -> park H-003 classical")
EOF
echo "[EXP-0016] OK: metrics.json written."
