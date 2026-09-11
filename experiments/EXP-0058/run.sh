#!/usr/bin/env bash
# Runner for EXP-0058 — threshold-hysteresis union probe on 05db0fb1.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05db0fb1"
FRAMES="20 21 22 23 24 25 26 27 28 29"

echo "[EXP-0058] 1/2: window detection @99.0 (anchors) + @95.0 (halo)..."
for t in $FRAMES; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 99.0 --out "$EXP_DIR/hi99_t${t}.json" > /dev/null
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 95.0 --out "$EXP_DIR/lo95_t${t}.json" > /dev/null
done
echo "  detection done (20 frames)"

echo "[EXP-0058] 2/2: match + fuse + verdict..."
python3 - "$EXP_DIR" "$ROOT" $FRAMES <<'EOF'
import json, os, sys, time
d, root = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3:]]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes
VX = (1.625, 0.40625, 0.40625)
GATE_UM = 3.0
SID = "6bba_05db0fb1"
t0 = time.time()

gt_full = json.load(open(os.path.join(
    root, "experiments/EXP-0003/gt", f"{SID}_gt.json")))
gt_win = [n for n in gt_full["nodes"] if int(n["t"]) in frames]
n_gt = len(gt_win)
assert n_gt > 0, "no GT in window"

def um(a, b):
    dz = (a["z"] - b["z"]) * VX[0]
    dy = (a["y"] - b["y"]) * VX[1]
    dx = (a["x"] - b["x"]) * VX[2]
    return (dz * dz + dy * dy + dx * dx) ** 0.5

def load(prefix):
    nodes, el, gid = [], [], 0
    for t in frames:
        blob = json.load(open(os.path.join(d, f"{prefix}_t{t}.json")))
        el.append(float(blob.get("params", {}).get("elapsed_s", 0.0)))
        for n in blob["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": int(n["t"]), "z": n["z"],
                          "y": n["y"], "x": n["x"]})
    return nodes, el

def stats(nodes):
    _, g2p = match_nodes(nodes, gt_win)
    return {"matched": len(g2p), "n_gt": n_gt,
            "recall": round(len(g2p) / n_gt, 4), "total_det": len(nodes),
            "det_per_frame": round(len(nodes) / len(frames), 1)}

hi, hi_el = load("hi99")
lo, lo_el = load("lo95")

# NMS-fuse per frame: anchors + halo detections >= GATE_UM from every anchor
union, gid = [], 0
n_halo_kept = n_halo_dropped = 0
for t in frames:
    a = [n for n in hi if n["t"] == t]
    h = [n for n in lo if n["t"] == t]
    keep = [w for w in h if all(um(w, v) >= GATE_UM for v in a)]
    n_halo_kept += len(keep)
    n_halo_dropped += len(h) - len(keep)
    for n in a + keep:
        gid += 1
        union.append({"id": gid, "t": t, "z": n["z"], "y": n["y"],
                      "x": n["x"]})

r_hi, r_lo, r_un = stats(hi), stats(lo), stats(union)
extra_matched = r_un["matched"] - r_lo["matched"]
extra_det = r_un["total_det"] - r_lo["total_det"]
cost = round(extra_det / extra_matched, 2) if extra_matched > 0 else None
go = bool(extra_matched >= 1 and cost is not None and cost <= 10.0)
verdict = ("GO" if go else "STOP")

# Overlap diagnostics: is @99 (near-)subset of @95 (monotonicity check)?
_, g2p_hi = match_nodes(hi, gt_win)
_, g2p_lo = match_nodes(lo, gt_win)
gt_lo = {g for g, _ in g2p_lo.items()}
rescued = sorted(g for g, _ in match_nodes(union, gt_win)[1].items()
                 if g not in gt_lo)

print(f"  @99.0 : recall={r_hi['recall']:.4f} ({r_hi['matched']}/{n_gt}) "
      f"det/f={r_hi['det_per_frame']} s/f={sum(hi_el)/len(hi_el):.2f}")
print(f"  @95.0 : recall={r_lo['recall']:.4f} ({r_lo['matched']}/{n_gt}) "
      f"det/f={r_lo['det_per_frame']} s/f={sum(lo_el)/len(lo_el):.2f}")
print(f"  union : recall={r_un['recall']:.4f} ({r_un['matched']}/{n_gt}) "
      f"det/f={r_un['det_per_frame']} halo kept/dropped="
      f"{n_halo_kept}/{n_halo_dropped}")
print(f"  extra_matched={extra_matched} extra_det={extra_det} "
      f"cost={cost} rescued_gt_ids={rescued} -> {verdict}")

metrics = {
    "exp_id": "EXP-0058",
    "title": "Threshold-hysteresis union probe on 05db0fb1",
    "hypothesis_id": "H-002",
    "protocol_version": "1.2",
    "real_data": True, "image_based": True,
    "scope": ("detection/recall-only window probe (no edges/linking); "
              "single-sample operating-point probe, HPs fixed a priori, "
              "no selection; ceiling keep-trying, NOT a promotion claim"),
    "sample": SID, "window": {"t0": 20, "t1": 29, "n_frames": len(frames)},
    "n_frames_detected": 2 * len(frames),
    "detector": {"script": "scripts/dog_detect.py", "sigmas": "base",
                 "min_size": 50, "thr_mode": "percentile"},
    "fusion": {"anchor_pct": 99.0, "halo_pct": 95.0, "gate_um": GATE_UM,
               "halo_kept": n_halo_kept, "halo_dropped": n_halo_dropped},
    "matcher": {"voxel_um": list(VX), "max_dist_um": 7.0},
    "configs": {
        "hi99": {**r_hi, "s_per_frame": round(sum(hi_el)/len(hi_el), 2)},
        "lo95": {**r_lo, "s_per_frame": round(sum(lo_el)/len(lo_el), 2)},
        "union": {**r_un},
    },
    "extra_matched": extra_matched, "extra_det": extra_det,
    "marginal_cost_per_match": cost,
    "rescued_gt_ids": rescued,
    "go_criterion": ("recall(union) > recall(@95) by >=1 GT node AND "
                     "extra_det/extra_matched <= 10"),
    "verdict": verdict,
    "decision": "keep-trying",
    "decision_reason": ("Window rung only; GO -> full-video follow-up rung, "
                        "not run here."),
    "wall_s": round(time.time() - t0, 1),
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0058] verdict={verdict} (metrics.json written)")
EOF
echo "[EXP-0058] OK."
