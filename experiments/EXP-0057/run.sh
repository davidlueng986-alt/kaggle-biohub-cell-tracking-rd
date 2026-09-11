#!/usr/bin/env bash
# Runner for EXP-0057 — 05db0fb1 full-video @94.5 descent probe.
# Single-sample operating-point test (NOT a promotion claim): HP fixed a priori
# at pct=94.5, single deterministic pass, no selection on this sample.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
# Pipeline: detect (100 frames @94.5) -> global re-id + link -> score -> metrics.json
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SID="6bba_05db0fb1"
PCT="94.5"

echo "[EXP-0057] 1/4: detect $SID t=0..99 @ $PCT ..."
for t in $(seq 0 99); do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${SID}.zarr" \
    --t "$t" --pct "$PCT" --out "$EXP_DIR/full_${SID}_t${t}.json" > /dev/null
done
echo "  detect done: $(ls "$EXP_DIR"/full_${SID}_t*.json | wc -l) frames"

echo "[EXP-0057] 2/4: global re-id + link (baseline_link defaults, gate 7um) ..."
python3 - "$EXP_DIR" "$ROOT" "$SID" <<'EOF'
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
pred = BL.link({"nodes": nodes, "edges": []})  # defaults: MAXD=7.0 um gate
json.dump(pred, open(os.path.join(d, f"{sid}_pred.json"), "w"))
print(f"  linked: {len(nodes)} nodes gid-unique, {len(pred['edges'])} edges "
      f"[{pred.get('assign')}]", flush=True)
EOF

echo "[EXP-0057] 3/4: score @94.5 (trusted scorer, runtime-only scipy solver) ..."
python3 -u "$EXP_DIR/score_fast.py"

echo "[EXP-0057] 4/4: assemble metrics.json (comparison vs frozen @95.0/@95.5/@96.0/@98.5 + verdict) ..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sc = json.load(open(os.path.join(d, "scores.json")))["p945"]
m56 = json.load(open(os.path.join(
    root, "experiments/EXP-0056/metrics.json")))["comparison"]
row950f = m56["@95.0"]
row955 = m56["@95.5_frozen"]
row96 = m56["@96.0_frozen"]
row98 = m56["@98.5_frozen"]
row945 = {"recall": sc["recall"], "det_f": sc["det_f"], "gid": sc["gid"],
          "raw": sc["raw"], "edge_adj": sc["edge"], "div": sc["div"],
          "score": sc["score"], "ec": sc["ec"], "dc": sc["dc"],
          "T_true": sc["T_true"], "T_ratio": sc["T_ratio"], "s_f": sc["s_f"],
          "assign": sc["assign"]}
# Verdict bar (mission-spec): meet-or-beat @95.0 on BOTH recall and adj.
REC_BAR, ADJ_BAR = 0.750, 0.5466
rec_ok = row945["recall"] >= REC_BAR
adj_ok = row945["edge_adj"] >= ADJ_BAR
verdict = "CONTINUE-DESCENT" if (rec_ok and adj_ok) else "STOP-DESCENT"
metrics = {
    "exp_id": "EXP-0057",
    "title": "05db0fb1 full-video @94.5 descent probe",
    "protocol_version": "1.2",
    "scorer_version": "1.1.0",
    "cv_tag": "single-sample operating-point test (NOT a promotion claim): "
              "single deterministic pass, HP fixed a priori at 94.5, "
              "no selection on this sample",
    "dry_run": False, "real_data": True, "image_based": True,
    "simplified_scorer": False,
    "sample": "6bba_05db0fb1", "frames": 100, "pct": 94.5,
    "T_true": 69800, "gt_divisions": 3,
    "linker": "baseline_link defaults (gate 7um, one-to-one, causal)",
    "comparison": {
        "@94.5": row945,
        "@95.0_frozen": row950f,
        "@95.5_frozen": row955,
        "@96.0_frozen": row96,
        "@98.5_frozen": row98,
        "delta_recall_vs950": row945["recall"] - row950f["recall"],
        "delta_raw_vs950": row945["raw"] - row950f["raw"],
        "delta_adj_vs950": row945["edge_adj"] - row950f["edge_adj"],
        "delta_score_vs950": row945["score"] - row950f["score"],
        "delta_T_ratio_vs950": row945["T_ratio"] - row950f["T_ratio"],
    },
    "verdict": verdict,
    "verdict_reason": (f"recall {'OK' if rec_ok else 'FELL'} "
                       f"({row945['recall']:.4f} vs bar {REC_BAR}) AND "
                       f"adj {'OK' if adj_ok else 'FELL'} "
                       f"({row945['edge_adj']:.4f} vs bar {ADJ_BAR})"),
    "division_readout": (f"div {row945['div']:.4f}, "
                         f"dc {row945['dc']['TP']}/{row945['dc']['FP']}/{row945['dc']['FN']}: "
                         "one-to-one linker predicts zero forks; "
                         "3 GT divisions all FN as expected"),
    "parity_watch": (f"T_ratio @94.5 = {row945['T_ratio']:.4f} "
                     f"(@95.0 was {row950f['T_ratio']:.4f}; watch level ~0.65)"),
    "status": "done",
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0057] verdict={verdict} "
      f"d_recall={metrics['comparison']['delta_recall_vs950']:+.4f} "
      f"d_adj={metrics['comparison']['delta_adj_vs950']:+.4f}")
EOF
echo "[EXP-0057] OK: metrics.json written."
