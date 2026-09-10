#!/usr/bin/env bash
# Runner for EXP-0021 — image-policy transfer, all 6 subset samples.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0021] 1/3: verify frozen reuse + fresh detection..."
# spot re-detection determinism gate (byte-equality before reuse)
for spec in "44b6_0113de3b:99.0:EXP-0008" "6bba_05b6850b:98.5:EXP-0009"; do
  sid="${spec%%:*}"; rest="${spec#*:}"; pct="${rest%%:*}"; src="${rest##*:}"
  python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
    --t 25 --pct "$pct" --out "$EXP_DIR/_spot_${sid}.json" > /dev/null
  python3 - "$EXP_DIR/_spot_${sid}.json" "$ROOT/experiments/${src}/full_${sid}_t25.json" <<'EOF'
import json, sys
a = json.load(open(sys.argv[1]))["nodes"]; b = json.load(open(sys.argv[2]))["nodes"]
# compare COORDINATE sets (dict schema evolved: split/parent keys added later;
# positions + count are the determinism contract; timing excluded as noise)
sa = sorted([(n["z"], n["y"], n["x"]) for n in a])
sb = sorted([(n["z"], n["y"], n["x"]) for n in b])
assert len(sa) == len(sb) and set(sa) == set(sb), \
    f"REUSE REFUSED: spot re-detect positions differ for {sys.argv[2]}"
print(f"  reuse verified identical positions: {sys.argv[2].split('/')[-2]} ({len(sa)} nodes)")
EOF
  rm "$EXP_DIR/_spot_${sid}.json"
done
# reuse frozen det files for reference samples
cp "$ROOT/experiments/EXP-0008"/full_44b6_0113de3b_t*.json "$EXP_DIR"/
cp "$ROOT/experiments/EXP-0009"/full_6bba_05b6850b_t*.json "$EXP_DIR"/
for spec in "44b6_0b24845f:99.0" "44b6_0c582fdc:99.0" "6bba_05db0fb1:98.5" "6bba_062c8d37:98.5"; do
  sid="${spec%%:*}"; pct="${spec##*:}"
  for t in $(seq 0 99); do
    python3 "$ROOT/scripts/dog_detect.py" "$ROOT/data/train/${sid}.zarr" \
      --t "$t" --pct "$pct" --out "$EXP_DIR/full_${sid}_t${t}.json" > /dev/null
  done
  echo "  $sid @ $pct done"
done

echo "[EXP-0021] 2/3: link + score all 6..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
from score import score_samples, match_nodes
SIDS = ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
        "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]
rows = {}
for sid in SIDS:
    gt = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    nodes, gid, times, recs = [], 0, [], []
    for t in range(100):
        det = json.load(open(os.path.join(d, f"full_{sid}_t{t}.json")))
        times.append(det["params"]["elapsed_s"])
        g = [n for n in gt["nodes"] if n["t"] == t]
        if g:
            _, g2p = match_nodes(det["nodes"], g)
            recs.append(len(g2p) / len(g))
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    pred = BL.link({"nodes": nodes, "edges": []})
    json.dump(pred, open(os.path.join(d, f"{sid}_pred.json"), "w"))
    agg = score_samples([(sid, pred, gt, None)])
    s = agg["per_sample"][0]
    rows[sid] = {"recall": sum(recs) / len(recs), "det_f": gid / 100,
                 "edge": s["adjusted_edge_jaccard"], "raw": s["edge_jaccard_raw"],
                 "div": s["division_jaccard"], "score": s["score"],
                 "ec": s["edge_counts"], "dc": s["division_counts"],
                 "T_true": s["T_true"], "T_ratio": gid / s["T_true"],
                 "s_f": sum(times) / len(times), "assign": pred.get("assign")}
    print(f"  {sid}: rec={rows[sid]['recall']:.3f} det/f={gid/100:.0f} "
          f"raw={s['edge_jaccard_raw']:.4f} adj={s['adjusted_edge_jaccard']:.4f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
          f"dc={s['division_counts']['TP']}/{s['division_counts']['FP']}/{s['division_counts']['FN']} "
          f"T={rows[sid]['T_ratio']:.2f} t={rows[sid]['s_f']:.2f}s/f [{pred.get('assign')}]", flush=True)
json.dump(rows, open(os.path.join(d, "rows.json"), "w"), indent=2)
EOF

echo "[EXP-0021] 3/3: embryo micros + transfer verdict..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
rows = json.load(open(os.path.join(d, "rows.json")))
S44 = [s for s in rows if s.startswith("44b6")]
S6B = [s for s in rows if s.startswith("6bba")]
def micro(keys):
    num = den = 0.0
    for s in keys:
        c = rows[s]["ec"]; w = c["TP"] + c["FP"] + c["FN"]
        num += rows[s]["edge"] * w; den += w
    return num / den
m44, m6b = micro(S44), micro(S6B)
checks = {f"{s}_rec": rows[s]["recall"] >= (0.95 if s.startswith("44b6") else 0.85) for s in rows}
checks["micro44_sane"] = m44 > 0.8
checks["micro6b_sane"] = m6b > 0.6
metrics = {"exp_id": "EXP-0021", "title": "Image-policy transfer, all 6",
           "hypothesis_id": "H-002", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": True, "simplified_scorer": False,
           "levels": {"44b6": 99.0, "6bba": 98.5},
           "per_sample": rows,
           "micros": {"44b6": m44, "6bba": m6b, "worst": min(m44, m6b)},
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Full-subset IMAGE baseline established (worst-fold image micro); transfer verdict per checks. "
                               "Baseline rung: keep-trying ceiling (single deterministic pass). "
                               "Next: beat this number (divisions on image path, timing).")}
assert True  # ledger records either verdict; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"micros: 44b6={m44:.4f} 6bba={m6b:.4f} worst={min(m44,m6b):.4f}")
print("checks:", checks)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0021] OK: metrics.json written."
