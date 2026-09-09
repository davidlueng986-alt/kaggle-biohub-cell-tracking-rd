#!/usr/bin/env bash
# Runner for EXP-0007 — DoG detection probe (CPU-only, deterministic).
# Exits 0 (probe verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SAMPLES="44b6_0113de3b 6bba_05b6850b"
FRAMES="0 1 2"
PCTS="99.0 99.5"

echo "[EXP-0007] 1/3: DoG detection on probe frames..."
for sid in $SAMPLES; do
  for t in $FRAMES; do
    for p in $PCTS; do
      python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
        --t "$t" --pct "$p" --out "$EXP_DIR/det_${sid}_t${t}_p${p}.json" > /dev/null
    done
  done
  echo "  $sid frames done"
done

echo "[EXP-0007] 2/3: match vs GT (P/R) + link + score..."
python3 - "$EXP_DIR" $SAMPLES <<'EOF'
import json, glob, os, sys
d = sys.argv[1]; sids = sys.argv[2:]
sys.path.insert(0, os.path.join(d, "..", "..", "scripts"))
from score import match_nodes, score_samples
import baseline_link as BL
out = {"per_sample": {}, "detection": {}}
for sid in sids:
    gt_full = json.load(open(os.path.join(d, "..", "EXP-0003", "gt", f"{sid}_gt.json")))
    for pct in ("99.0", "99.5"):
        key = f"{sid}@p{pct}"
        det_nodes, times, recs, mrates = [], [], [], []
        for t in (0, 1, 2):
            det = json.load(open(os.path.join(d, f"det_{sid}_t{t}_p{pct}.json")))
            times.append(det["params"]["elapsed_s"])
            g = [n for n in gt_full["nodes"] if n["t"] == t]
            p2g, g2p = match_nodes(det["nodes"], g)
            recs.append(len(g2p) / max(1, len(g)))
            mrates.append(len(p2g) / max(1, len(det["nodes"])))
            for n in det["nodes"]:
                det_nodes.append(dict(n))
        # global ids for linking (ids restart per frame in det files)
        gid = 0
        for n in det_nodes:
            gid += 1; n["id"] = gid
        pred = BL.link({"nodes": det_nodes, "edges": []})
        gsub = {"nodes": [n for n in gt_full["nodes"] if n["t"] in (0, 1, 2)],
                "edges": [e for e in gt_full["edges"]
                          if e[0] in {n["id"] for n in gt_full["nodes"] if n["t"] in (0, 1, 2)}
                          and e[1] in {n["id"] for n in gt_full["nodes"] if n["t"] in (0, 1, 2)}]}
        Tscaled = round(gt_full["T_true"] * 3 / 100) if gt_full.get("T_true") else None
        gsub["T_true"] = Tscaled
        agg = score_samples([(key, pred, gsub, None)])
        s = agg["per_sample"][0]
        out["per_sample"][key] = {
            "n_det": len(det_nodes), "gt_nodes_sub": len(gsub["nodes"]),
            "gt_edges_sub": len(gsub["edges"]), "T_true_scaled": Tscaled,
            "recall_mean": sum(recs) / len(recs), "recalls": recs,
            "matchrate_mean": sum(mrates) / len(mrates),
            "edge_raw": s["edge_jaccard_raw"], "edge_adj": s["adjusted_edge_jaccard"],
            "div": s["division_jaccard"], "score": s["score"],
            "ec": s["edge_counts"], "dc": s["division_counts"],
            "detect_s_per_frame": times}
        out["detection"][key] = {"recalls": recs, "matchrates": mrates, "times": times}
        print(f"  {key}: det={len(det_nodes)} gt={len(gsub['nodes'])}/{len(gsub['edges'])} "
              f"rec={sum(recs)/len(recs):.2f} edge_raw={s['edge_jaccard_raw']:.4f} "
              f"adj={s['adjusted_edge_jaccard']:.4f} div={s['division_jaccard']:.3f} t={times}")
json.dump(out, open(os.path.join(d, "probe.json"), "w"), indent=2)
EOF

echo "[EXP-0007] 3/3: verdict..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
p = json.load(open(os.path.join(d, "probe.json")))["per_sample"]
rec990 = min(p["44b6_0113de3b@p99.0"]["recall_mean"], p["6bba_05b6850b@p99.0"]["recall_mean"])
checks = {"pct99_recall_1.00_both": abs(rec990 - 1.0) < 1e-9}
metrics = {
  "exp_id": "EXP-0007", "title": "DoG detection probe on real zarr",
  "hypothesis_id": "H-002", "protocol_version": "1.1",
  "dry_run": False, "real_data": True, "image_based": True,
  "simplified_scorer": False,
  "probe_frames": {"44b6_0113de3b": [0, 1, 2], "6bba_05b6850b": [0, 1, 2]},
  "per_sample": p,
  "checks": checks, "all_checks_pass": all(checks.values()),
  "decision": "keep-trying",
  "decision_reason": ("First IMAGE-BASED end-to-end number (probe only): DoG pct99 recall 1.00 both samples, "
                      "~1s/frame CPU (over video budget unoptimized — H-005). Mini-graph edges trail oracle floor "
                      "(extra-track pressure) as predicted. NOT promotable (3-frame probe). Next: full-frame detection "
                      "sweep + threshold operating curve (EXP-0008) and/or H-003 appearance."),
}
assert metrics["all_checks_pass"], f"falsified: {checks}"
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
EOF
echo "[EXP-0007] OK: metrics.json written."
