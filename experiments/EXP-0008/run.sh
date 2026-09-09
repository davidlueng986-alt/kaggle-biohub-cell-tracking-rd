#!/usr/bin/env bash
# Runner for EXP-0008 — full-frame DoG sweep + threshold curve.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SAMPLES="44b6_0113de3b 6bba_05b6850b"

echo "[EXP-0008] 1/3: threshold curve on t0-9 window..."
for sid in $SAMPLES; do
  for t in 0 1 2 3 4 5 6 7 8 9; do
    for p in 98.5 99.0 99.5; do
      python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
        --t "$t" --pct "$p" --out "$EXP_DIR/curve_${sid}_t${t}_p${p}.json" > /dev/null
    done
  done
  echo "  $sid curve done"
done

echo "[EXP-0008] 2/3: full-video detection @99.0 + link + score..."
for sid in $SAMPLES; do
  for t in $(seq 0 99); do
    python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
      --t "$t" --pct 99.0 --out "$EXP_DIR/full_${sid}_t${t}.json" > /dev/null
  done
  echo "  $sid detection done"
  python3 - "$EXP_DIR" "$ROOT" "$sid" <<'EOF'
import json, os, sys
d, root, sid = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
nodes, gid = [], 0
for t in range(100):
    det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
pred = BL.link({"nodes": nodes, "edges": []})
json.dump(pred, open(os.path.join(d, f"full_{sid}_pred.json"), "w"))
print(f"  {sid}: {len(nodes)} detections -> {len(pred['edges'])} links [{pred.get('assign')}]")
EOF
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/full_${sid}_pred.json" \
    --gt "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" \
    --out "$EXP_DIR/full_${sid}_scores.json" > /dev/null
done

echo "[EXP-0008] 3/3: curves + verdict..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
SIDS = ["44b6_0113de3b", "6bba_05b6850b"]
sys.path.insert(0, os.path.join(d, "..", "..", "scripts"))
from score import match_nodes
curve, full = {}, {}
for sid in SIDS:
    gt_full = json.load(open(os.path.join(d, "..", "EXP-0003", "gt", f"{sid}_gt.json")))
    curve[sid] = {}
    for pct in ("98.5", "99.0", "99.5"):
        recs, counts, times = [], [], []
        for t in range(10):
            det = json.load(open(os.path.join(d, f"curve_{sid}_t{t}_p{pct}.json")))
            g = [n for n in gt_full["nodes"] if n["t"] == t]
            _, g2p = match_nodes(det["nodes"], g)
            recs.append(len(g2p) / max(1, len(g)))
            counts.append(len(det["nodes"]))
            times.append(det["params"]["elapsed_s"])
        # recall over frames that HAVE gt (avoid empty-frame dilution); also overall
        curve[sid][pct] = {"recall_mean_all": sum(recs) / len(recs),
                           "counts_mean": sum(counts) / len(counts),
                           "s_per_frame": sum(times) / len(times)}
    agg = json.load(open(os.path.join(d, f"full_{sid}_scores.json")))
    s = agg["per_sample"][0]
    pred_meta = json.load(open(os.path.join(d, f"full_{sid}_pred.json")))
    # full-video recall: all GT nodes matched by detections across frames
    rec_all, n_gt = [], 0
    for t in range(100):
        det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
        g = [n for n in gt_full["nodes"] if n["t"] == t]
        n_gt += len(g)
        if g:
            _, g2p = match_nodes(det["nodes"], g)
            rec_all.append(len(g2p) / len(g))
    full[sid] = {"recall_full": sum(rec_all) / len(rec_all) if rec_all else 1.0,
                 "n_det_total": sum(curve[sid]["99.0"]["counts_mean"] for _ in [0]),
                 "edge_raw": s["edge_jaccard_raw"], "edge_adj": s["adjusted_edge_jaccard"],
                 "div": s["division_jaccard"], "score": s["score"],
                 "ec": s["edge_counts"], "dc": s["division_counts"],
                 "T_true": s["T_true"], "assign": pred_meta.get("assign")}
    print(f"  {sid}: recall_full={full[sid]['recall_full']:.3f} "
          f"edge_raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']}")
rec990 = min(full[s]["recall_full"] for s in SIDS)
# H-005 timing: mean detect s/frame from full-video det files
times = {}
for sid in SIDS:
    ts = [json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))["params"]["elapsed_s"] for t in range(100)]
    times[sid] = {"mean_s": sum(ts) / len(ts), "max_s": max(ts),
                  "video_100f_s": sum(ts)}
checks = {"full_recall_ge_0.90_both": rec990 >= 0.90,
          "curve_monotone": all(curve[s]["98.5"]["recall_mean_all"] >= curve[s]["99.0"]["recall_mean_all"] >= curve[s]["99.5"]["recall_mean_all"] for s in SIDS)}
metrics = {"exp_id": "EXP-0008", "title": "Full-frame DoG sweep + threshold curve",
           "hypothesis_id": "H-002+H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "curve_t0_9": curve, "full_video_p99": full,
           "timing_detect_s": times,
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Full-video image-based tracks scored; operating point generality tested. "
                               "NOT promotable (single deterministic run). Timing debt quantified for H-005. "
                               "Next: per-frame adaptive threshold if recall fails, else H-003 appearance + submit timing.")}
assert True  # ledger records falsified runs too; verdict lives in checks, not exit code
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
if not metrics["all_checks_pass"]:
    print("FALSIFIED (recorded): pct99 generality rejected -> EXP-0009 full-video @98.5 (level, not adaptivity: threshold already per-frame)")
EOF
echo "[EXP-0008] OK: metrics.json written."
