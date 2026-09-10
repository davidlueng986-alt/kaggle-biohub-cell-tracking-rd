#!/usr/bin/env bash
# Runner for EXP-0023 — full-video downsampled DoG (DS) both samples.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
#
# Pipeline per sample (operating points frozen from EXP-0008/EXP-0009):
#   44b6_0113de3b @99.0 DS + 6bba_05b6850b @98.5 DS, t=0..99, --downsample 2
#   -> global re-id per video -> baseline_link -> score.py vs full GT
# References are RECOMPUTED from artifacts (never pasted):
#   full-res preds: EXP-0008/full_44b6_0113de3b_pred.json (@99.0),
#                   EXP-0009/full_6bba_05b6850b_pred.json (@98.5)
#   full-res dets:  EXP-0008/full_<sid>_t<t>.json, EXP-0009/full_<sid>_t<t>.json
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0023] 1/3: full-video DS detection..."
for t in $(seq 0 99); do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/44b6_0113de3b.zarr" \
    --t "$t" --pct 99.0 --downsample 2 --out "$EXP_DIR/ds_44b6_0113de3b_t${t}.json" > /dev/null
done
echo "  44b6_0113de3b DS @99.0 done"
for t in $(seq 0 99); do
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/6bba_05b6850b.zarr" \
    --t "$t" --pct 98.5 --downsample 2 --out "$EXP_DIR/ds_6bba_05b6850b_t${t}.json" > /dev/null
done
echo "  6bba_05b6850b DS @98.5 done"

echo "[EXP-0023] 2/3: global re-id + link + score..."
for sid in 44b6_0113de3b 6bba_05b6850b; do
  python3 - "$EXP_DIR" "$ROOT" "$sid" <<'EOF'
import json, os, sys
d, root, sid = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
nodes, gid = [], 0
for t in range(100):
    det = json.load(open(os.path.join(d, f"ds_{sid}_t{t}.json")))
    for n in det["nodes"]:
        gid += 1
        nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
pred = BL.link({"nodes": nodes, "edges": []})
json.dump(pred, open(os.path.join(d, f"ds_{sid}_pred.json"), "w"))
print(f"  {sid}: {len(nodes)} detections -> {len(pred['edges'])} links [{pred.get('assign')}]", flush=True)
EOF
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/ds_${sid}_pred.json" \
    --gt "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" \
    --out "$EXP_DIR/ds_${sid}_scores.json" > /dev/null
done

echo "[EXP-0023] 3/3: metrics + recomputed refs + GO/STOP verdict..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
from score import match_nodes, score_samples

CFG = {"44b6_0113de3b": {"pct": 99.0, "ref_exp": "EXP-0008", "ref_pred": "full_44b6_0113de3b_pred.json",
                         "ref_det_pat": "full_44b6_0113de3b_t{t}.json"},
       "6bba_05b6850b": {"pct": 98.5, "ref_exp": "EXP-0009", "ref_pred": "full_6bba_05b6850b_pred.json",
                         "ref_det_pat": "full_6bba_05b6850b_t{t}.json"}}

def frame_recall(det_nodes, gt_nodes):
    """(micro_matched, micro_total, macro_mean): per-frame match_nodes."""
    m_n, m_d, macro = 0, 0, []
    # per-frame matching
    import collections
    gb = collections.defaultdict(list)
    for n in gt_nodes:
        gb[n["t"]].append(n)
    pb = collections.defaultdict(list)
    for n in det_nodes:
        pb[n["t"]].append(n)
    for t, g in gb.items():
        _, g2p = match_nodes(pb.get(t, []), g)
        m_n += len(g2p); m_d += len(g)
        macro.append(len(g2p) / len(g))
    return m_n / m_d if m_d else 1.0, (sum(macro) / len(macro) if macro else 1.0)

rows, ref = {}, {}
for sid, c in CFG.items():
    gt = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    agg = json.load(open(os.path.join(d, f"ds_{sid}_scores.json")))
    s = agg["per_sample"][0]
    # DS stats from DS det files
    det_all, times, counts = [], [], []
    for t in range(100):
        det = json.load(open(os.path.join(d, f"ds_{sid}_t{t}.json")))
        times.append(det["params"]["elapsed_s"]); counts.append(len(det["nodes"]))
        det_all.extend([{**n, "t": t} for n in det["nodes"]])
    rec_micro, rec_macro = frame_recall(det_all, gt["nodes"])
    # recompute full-res reference: re-score ref pred + recall from ref det files
    rdir = os.path.join(root, "experiments", c["ref_exp"])
    rpred = json.load(open(os.path.join(rdir, c["ref_pred"])))
    ragg = score_samples([("ref", rpred, gt, None)])
    rs = ragg["per_sample"][0]
    fdet_all = []
    for t in range(100):
        p = os.path.join(rdir, c["ref_det_pat"].format(t=t))
        if os.path.exists(p):
            fdet = json.load(open(p))
            fdet_all.extend([{**n, "t": t} for n in fdet["nodes"]])
    r_micro, r_macro = frame_recall(fdet_all, gt["nodes"])
    ref[sid] = {"recall_micro": r_micro, "recall_macro": r_macro,
                "edge_raw": rs["edge_jaccard_raw"], "edge_adj": rs["adjusted_edge_jaccard"],
                "div": rs["division_jaccard"], "ec": rs["edge_counts"],
                "T_pred": rs["T_pred"], "source": f"{c['ref_exp']}/{c['ref_pred']} (re-scored)"}
    pred = json.load(open(os.path.join(d, f"ds_{sid}_pred.json")))
    rows[sid] = {"pct": c["pct"], "downsample": 2,
                 "recall_micro": rec_micro, "recall_macro": rec_macro,
                 "det_per_frame": sum(counts) / len(counts), "n_det_total": sum(counts),
                 "edge_raw": s["edge_jaccard_raw"], "edge_adj": s["adjusted_edge_jaccard"],
                 "div": s["division_jaccard"], "score": s["score"],
                 "ec": s["edge_counts"], "dc": s["division_counts"],
                 "T_pred": s["T_pred"], "T_true": s["T_true"],
                 "T_ratio": sum(counts) / s["T_true"],
                 "n_pred_edges": len(pred["edges"]),
                 "s_per_frame": sum(times) / len(times),
                 "det_s_total_100f": round(sum(times), 1),
                 "assign": pred.get("assign")}
    print(f"  {sid} DS: rec_micro={rec_micro:.4f} (ref {r_micro:.4f}) "
          f"rec_macro={rec_macro:.4f} (ref {r_macro:.4f}) det/f={rows[sid]['det_per_frame']:.1f} "
          f"raw={s['edge_jaccard_raw']:.4f} (ref {rs['edge_jaccard_raw']:.4f}) "
          f"adj={s['adjusted_edge_jaccard']:.4f} (ref {rs['adjusted_edge_jaccard']:.4f}) "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
          f"T_ratio={rows[sid]['T_ratio']:.3f} {rows[sid]['s_per_frame']:.2f}s/f [{pred.get('assign')}]",
          flush=True)

checks = {}
for sid in CFG:
    r, w = ref[sid], rows[sid]
    checks[f"{sid}_recall_within_0.01"] = w["recall_micro"] >= r["recall_micro"] - 0.01
    checks[f"{sid}_raw_within_0.005"] = w["edge_raw"] >= r["edge_raw"] - 0.005
    checks[f"{sid}_adj_ge_ref"] = w["edge_adj"] >= r["edge_adj"] - 1e-12
go = all(checks.values())
mean_spf = sum(rows[s]["s_per_frame"] for s in rows) / len(rows)
metrics = {"exp_id": "EXP-0023", "title": "Full-video DS both samples",
           "hypothesis_id": "H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "rows": rows, "reference_recomputed": ref, "checks": checks,
           "verdict": "GO" if go else "STOP",
           "timing": {"mean_s_per_frame": mean_spf,
                      "projected_s_per_video_100f": {s: rows[s]["det_s_total_100f"] for s in rows}},
           "decision": "go-kernel-upgrade" if go else "keep-trying",
           "decision_reason": ("GO kernel upgrade: DS recall/raw/adj hold per-sample vs recomputed "
                               "full-res refs." if go else
                               "STOP: DS fails a gate vs recomputed full-res refs; no kernel upgrade.")}
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
print("VERDICT:", "GO" if go else "STOP")
for k, v in checks.items():
    if not v:
        print("FAILED GATE:", k)
EOF
echo "[EXP-0023] OK: metrics.json written."
