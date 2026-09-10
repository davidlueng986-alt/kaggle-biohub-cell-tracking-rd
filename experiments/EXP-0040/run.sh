#!/usr/bin/env bash
# Runner for EXP-0040 — replicate @96 dark-sample recall gain on
# 44b6_0b24845f + 44b6_0c582fdc full-video (100 frames each @96.0).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
# Pipeline: detect (2x100 frames @96.0) -> global re-id + link -> score -> metrics.json
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
PCT="96.0"
SIDS="44b6_0b24845f 44b6_0c582fdc"

echo "[EXP-0040] 1/4: detect 2 samples x 100 frames @ $PCT ..."
for sid in $SIDS; do
  for t in $(seq 0 99); do
    python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
      --t "$t" --pct "$PCT" --out "$EXP_DIR/full_${sid}_t${t}.json" > /dev/null
  done
  echo "  $sid done: $(ls "$EXP_DIR"/full_${sid}_t*.json | wc -l) frames"
done

echo "[EXP-0040] 2/4: global re-id + link per video (baseline_link defaults, gate 7um) ..."
python3 - "$EXP_DIR" "$ROOT" $SIDS <<'EOF'
import json, os, sys
d, root, sids = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
for sid in sids:
    nodes, gid = [], 0
    for t in range(100):
        det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    pred = BL.link({"nodes": nodes, "edges": []})  # defaults: MAXD=7.0 um gate
    json.dump(pred, open(os.path.join(d, f"{sid}_pred.json"), "w"))
    print(f"  linked {sid}: {len(nodes)} nodes gid-unique, "
          f"{len(pred['edges'])} edges [{pred.get('assign')}]", flush=True)
EOF

echo "[EXP-0040] 3/4: score @96.0 + rescore @99.0 frozen baselines ..."
python3 -u "$EXP_DIR/score_fast.py"

echo "[EXP-0040] 4/4: assemble metrics.json (comparison table + verdicts) ..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sc = json.load(open(os.path.join(d, "scores.json")))
base = json.load(open(os.path.join(
    root, "experiments/EXP-0021/metrics.json")))["per_sample"]

samples, n_rep = {}, 0
for sid in ("44b6_0b24845f", "44b6_0c582fdc"):
    s = sc["samples"][sid]
    row96 = s["p96"]
    b = base[sid]
    # bars: recomputed-by-rescoring (fresh scorer run on frozen EXP-0021 pred)
    bar = {"recall": None, "det_f": b["det_f"],
           "raw": s["p99_rescored"]["raw"], "edge_adj": s["p99_rescored"]["edge"],
           "div": s["p99_rescored"]["div"], "score": s["p99_rescored"]["score"],
           "ec": s["p99_rescored"]["ec"], "dc": s["p99_rescored"]["dc"],
           "T_true": s["p99_rescored"]["T_true"],
           "T_ratio": s["p99_rescored"]["T_ratio"],
           "T_pred": s["p99_rescored"]["T_pred"],
           "rescore_match_ledger": (
               abs(s["p99_rescored"]["raw"] - b["raw"]) < 1e-9
               and abs(s["p99_rescored"]["edge"] - b["edge"]) < 1e-9),
           "ledger": {"recall": b["recall"], "det_f": b["det_f"],
                      "raw": b["raw"], "edge": b["edge"], "div": b["div"],
                      "score": b["score"], "ec": b["ec"], "dc": b["dc"],
                      "T_true": b["T_true"], "T_ratio": b["T_ratio"],
                      "s_f": b["s_f"], "assign": b["assign"]}}
    d_rec = row96["recall"] - b["recall"]
    d_raw = row96["raw"] - bar["raw"]
    d_adj = row96["edge"] - bar["edge_adj"]
    rep = (row96["recall"] >= b["recall"] + 0.10) and (row96["edge"] >= bar["edge_adj"])
    verdict = "REPLICATES" if rep else "DIVERGES"
    n_rep += int(rep)
    samples[sid] = {
        "@96.0": row96, "@99.0_bar_rescored": bar,
        "delta_recall_vs_ledger": d_rec, "delta_raw": d_raw, "delta_adj": d_adj,
        "criterion": {"recall_gain_ge_0.10": d_rec >= 0.10, "adj_ge_bar": d_adj >= 0},
        "verdict": verdict,
        "verdict_reason": (f"recall {row96['recall']:.4f} vs bar {b['recall']:.4f} "
                           f"(d={d_rec:+.4f}, need +0.10) AND adj {row96['edge']:.4f} "
                           f"vs bar {bar['edge_adj']:.4f} (d={d_adj:+.4f}, need >=0)"),
        "mechanism": {"T_ratio_96": row96["T_ratio"], "T_ratio_99": bar["T_ratio"],
                      "det_f_96": row96["det_f"], "det_f_99": bar["det_f"]},
    }

overall = "GO" if n_rep == 2 else ("MIXED" if n_rep == 1 else "STOP")
metrics = {
    "exp_id": "EXP-0040",
    "title": "Replicate @96 dark-sample recall gain on 0b24845f + 0c582fdc full-video",
    "hypothesis_id": "H-002-followup-replication",
    "protocol_version": "1.1",
    "scorer_version": sc["scorer"]["scorer_version"],
    "dry_run": False, "real_data": True, "image_based": True,
    "simplified_scorer": False,
    "samples": ["44b6_0b24845f", "44b6_0c582fdc"], "frames": 100,
    "pct_test": 96.0, "pct_bar": 99.0,
    "linker": "baseline_link defaults (gate 7um, one-to-one, causal)",
    "scorer_solver": sc["scorer"],
    "per_sample": samples,
    "overall": overall,
    "overall_reason": (f"{n_rep}/2 REPLICATES: " +
                       ", ".join(f"{k}={v['verdict']}" for k, v in samples.items())),
    "policy_note": ("GO -> recommend @96 as dark-sample policy rung EXP-0041 (do not run); "
                    "MIXED -> sample-specific, note which; STOP -> @96 does not generalize beyond 05db0fb1"),
    "status": "done",
}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0040] overall={overall} "
      + " ".join(f"{k}={v['verdict']}" for k, v in samples.items()))
EOF
echo "[EXP-0040] OK: metrics.json written."
