#!/usr/bin/env bash
# Runner for EXP-0026 — ROI-masked DoG acceleration (window gate).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if STOP).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05b6850b"
BLOCKS="20 21 22 23 24 25 26 27 28 29 40 41 42 43 44 45 46 47 48 49"

echo "[EXP-0026] 1/4: FULL window detect @98.5 (fresh reference)..."
T0=$(date +%s.%N)
for t in $BLOCKS; do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct 98.5 --out "$EXP_DIR/FULL_t${t}.json" > /dev/null
done
T1=$(date +%s.%N)
echo "  FULL done"

echo "[EXP-0026] 2/4: ROI window detect q=98 (primary) + q=95 (Pareto)..."
for t in $BLOCKS; do
  python3 "$EXP_DIR/roi_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --q 98 --pct 98.5 --out "$EXP_DIR/ROI_t${t}.json" > /dev/null
done
T2=$(date +%s.%N)
for t in $BLOCKS; do
  python3 "$EXP_DIR/roi_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --q 95 --pct 98.5 --out "$EXP_DIR/ROI95_t${t}.json" > /dev/null
done
T3=$(date +%s.%N)
echo "  ROI done"
echo "[EXP-0026] wall clocks: FULL=$T0..$T1 ROI98=$T1..$T2 ROI95=$T2..$T3"
echo "$T0 $T1 $T2 $T3" > "$EXP_DIR/.wall.txt"

echo "[EXP-0026] 3/4: micro-profile (t20: full DoG-vs-label, ROI shares)..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys, time
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
sys.path.insert(0, d)
import numpy as np, zarr
from scipy.ndimage import gaussian_filter, label
from roi_detect import roi_detect
from dog_detect import SIG_SMALL, SIG_LARGE
vol = np.asarray(zarr.open_group(os.path.join(root, "data/train/6bba_05b6850b.zarr"), mode="r")["0"][20])
# full-frame DoG vs threshold+label split
t0 = time.perf_counter()
g1 = gaussian_filter(vol.astype(np.float32), SIG_SMALL)
g2 = gaussian_filter(vol.astype(np.float32), SIG_LARGE)
dog = g1 - g2
t_dog = time.perf_counter() - t0
t0 = time.perf_counter()
thr = float(np.percentile(dog, 98.5))
bw = dog >= thr
lab, n = label(bw)
sizes = np.bincount(lab.ravel())
t_lab = time.perf_counter() - t0
t0 = time.perf_counter()  # per-component argwhere scans (detect() lines 68-77)
kept = 0
for i in range(1, n + 1):
    if 50 <= int(sizes[i]) <= 50000:
        np.argwhere(lab == i)
        kept += 1
t_arg = time.perf_counter() - t0
# ROI shares (mask vs per-box loop) from a fresh instrumented call
nodes, p = roi_detect(vol, q=98.0, pct=98.5)
prof = {"full_t20": {"gauss_pair_s": round(t_dog, 3),
                     "pct_label_s": round(t_lab, 3),
                     "percomp_argwhere_s": round(t_arg, 3),
                     "n_components": int(n), "n_kept": int(kept),
                     "argwhere_share": round(t_arg / (t_dog + t_lab + t_arg), 3)},
        "roi_q98_t20": {"mask_s": p["mask_s"], "det_loop_s": p["loop_s"],
                        "det_inner_s": p["det_s"], "nbox": p["nbox"],
                        "vox_frac": p["vox_frac"],
                        "mask_share": round(p["mask_s"] / p["elapsed_s"], 3)}}
json.dump(prof, open(os.path.join(d, ".profile.json"), "w"), indent=2)
print("  profile:", json.dumps(prof))
EOF

echo "[EXP-0026] 4/4: recall + link blocks + score + gate..."
WALL=$(cat "$EXP_DIR/.wall.txt")
python3 - "$EXP_DIR" "$ROOT" $BLOCKS <<EOF
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3:]]
WALL = "$WALL".split()
t0, t1, t2, t3 = map(float, WALL)
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
gt_full = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
gset = {n["id"] for n in gt_full["nodes"] if n["t"] in frames}
gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in frames],
        "edges": [e for e in gt_full["edges"] if e[0] in gset and e[1] in gset],
        "T_true": round((gt_full["T_true"] or 0) * len(frames) / 100)}
print(f"  GT subgraph: {len(gsub['nodes'])} nodes {len(gsub['edges'])} edges T~{gsub['T_true']}")
cfgs = {"FULL": "FULL", "ROI_q98": "ROI", "ROI_q95": "ROI95"}
res, times = {}, {"FULL": (t1 - t0) / len(frames),
                  "ROI_q98": (t2 - t1) / len(frames),
                  "ROI_q95": (t3 - t2) / len(frames)}
for tag, pre in cfgs.items():
    nodes, gid, rec_n, rec_d = [], 0, 0, 0
    for t in frames:
        det = json.load(open(os.path.join(d, f"{pre}_t{t}.json")))
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        _, g2p = match_nodes(det["nodes"], g)
        rec_n += len(g2p); rec_d += len(g)
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    pred = BL.link({"nodes": nodes, "edges": []})
    agg = score_samples([(tag, pred, gsub, None)])
    s = agg["per_sample"][0]
    res[tag] = {"recall": rec_n / rec_d, "rec_n": rec_n, "rec_d": rec_d,
                "n_det": len(nodes), "raw": s["edge_jaccard_raw"],
                "adj": s["adjusted_edge_jaccard"], "ec": s["edge_counts"],
                "s_per_frame": round(times[tag], 3)}
    e = s["edge_counts"]
    print(f"  {tag}: rec={rec_n/rec_d:.4f} det={len(nodes)} "
          f"raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={e['TP']}/{e['FP']}/{e['FN']} {times[tag]:.3f}s/f")
f, r = res["FULL"], res["ROI_q98"]
speedup = times["FULL"] / times["ROI_q98"]
go = bool(r["recall"] >= f["recall"] - 0.01
          and r["raw"] >= f["raw"] - 0.005
          and speedup >= 2.0)
print(f"  gate: dRecall={r['recall']-f['recall']:+.4f} (tol -0.01) "
      f"dRaw={r['raw']-f['raw']:+.4f} (tol -0.005) speedup={speedup:.2f}x -> {'GO' if go else 'STOP'}")
prof = json.load(open(os.path.join(d, ".profile.json")))
metrics = {"exp_id": "EXP-0026", "title": "ROI-masked DoG acceleration",
           "hypothesis_id": "H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True,
           "simplified_scorer": False, "blocks": frames,
           "detector": "scripts/dog_detect.py UNMODIFIED via roi_detect.py wrapper",
           "configs": res, "speedup_roi_q98_vs_full": round(speedup, 3),
           "speedup_roi_q95_vs_full": round(times["FULL"] / times["ROI_q95"], 3),
           "timing_breakdown": prof,
           "gate": {"recall_tol": 0.01, "raw_tol": 0.005, "speedup_min": 2.0,
                    "d_recall": round(r["recall"] - f["recall"], 4),
                    "d_raw": round(r["raw"] - f["raw"], 4),
                    "pass": go},
           "decision": "GO-full-video-EXP-0028" if go else "STOP",
           "decision_reason": ("PASS: ROI parity + >=2x -> recommend EXP-0028 full-video (not run here)."
                               if go else "FAIL: ROI does not meet parity+speed gate -> no full-video commit; EXP-0028 stays a recommendation only.")}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("gate pass:", go)
if not go:
    print("STOP (recorded): no full-video commit")
EOF
rm -f "$EXP_DIR/.wall.txt" "$EXP_DIR/.profile.json"
echo "[EXP-0026] OK: metrics.json written."
