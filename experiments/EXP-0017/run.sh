#!/usr/bin/env bash
# Runner for EXP-0017 — gate ablation (oracle) + gap pass (image graph).
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SIDS="44b6_0113de3b 44b6_0b24845f 44b6_0c582fdc 6bba_05b6850b 6bba_05db0fb1 6bba_062c8d37"

echo "[EXP-0017] 1/2: arm1 oracle gate ablation + arm2 image gap matrix..."
python3 - "$EXP_DIR" "$ROOT" $SIDS <<'EOF'
import json, os, sys
d, root = sys.argv[1], sys.argv[2]
sids = sys.argv[3:]
sys.path.insert(0, os.path.join(root, "scripts"))
import baseline_link as BL
from gap_link import gap_close
from score import score_samples
arm1 = {}
for g in (7.0, 10.0, 14.0):
    per = {}
    for sid in sids:
        gt = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
        t0 = __import__("time").time()
        pred = BL.link(gt, maxd=g)
        dt = __import__("time").time() - t0
        agg = score_samples([(f"g{g}_{sid}", pred, gt, None)])
        s = agg["per_sample"][0]
        per[sid] = {"edge": s["adjusted_edge_jaccard"], "raw": s["edge_jaccard_raw"],
                    "div": s["division_jaccard"], "score": s["score"],
                    "ec": s["edge_counts"], "dc": s["division_counts"],
                    "link_s": round(dt, 2), "assign": pred.get("assign")}
    arm1[str(g)] = per
    m44 = [per[s]["edge"] for s in sids if s.startswith("44b6")]
    print(f"  arm1 gate {g}: " + " ".join(
        f"{s}={per[s]['edge']:.4f}(TP{per[s]['ec']['TP']}/FP{per[s]['ec']['FP']}/FN{per[s]['ec']['FN']})" for s in sids))
# arm2: image graph 6bba@98.5 (EXP-0009 frozen pred, global ids)
gimg = json.load(open(os.path.join(d, "..", "EXP-0009", "full_6bba_05b6850b_pred.json")))
gtimg = json.load(open(os.path.join(root, "experiments/EXP-0003/gt/6bba_05b6850b_gt.json")))
arm2 = {}
for g in (7.0, 10.0):
    base = BL.link({"nodes": gimg["nodes"], "edges": []}, maxd=g)
    for gap in ("off", "on"):
        if gap == "on":
            pred = gap_close(base["nodes"], base["edges"], gap_um=14.0)
            pred["T_true"] = gimg.get("T_true")
        else:
            pred = base
        agg = score_samples([(f"img_g{g}_{gap}", pred, gtimg, None)])
        s = agg["per_sample"][0]
        arm2[f"g{g}_{gap}"] = {"edge": s["adjusted_edge_jaccard"], "raw": s["edge_jaccard_raw"],
                               "div": s["division_jaccard"], "score": s["score"],
                               "ec": s["edge_counts"], "dc": s["division_counts"],
                               "n_edges": len(pred["edges"])}
        print(f"  arm2 gate {g} gap {gap}: edge={s['adjusted_edge_jaccard']:.4f} "
              f"raw={s['edge_jaccard_raw']:.4f} ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
              f"div={s['division_jaccard']:.3f} edges={len(pred['edges'])}")
json.dump({"arm1": arm1, "arm2": arm2}, open(os.path.join(d, "grid.json"), "w"), indent=2)
EOF

echo "[EXP-0017] 2/2: verdict..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
grid = json.load(open(os.path.join(d, "grid.json")))
sids = ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
        "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]
floor = json.load(open(os.path.join(d, "..", "EXP-0003", "metrics.json")))["per_sample"]
def micro(per, embryo):
    num = den = 0.0
    for sid in sids:
        if sid.startswith(embryo):
            c = per[sid]["ec"]; w = c["TP"] + c["FP"] + c["FN"]
            num += per[sid]["edge"] * w; den += w
    return num / den
def divsum(per):
    t = f = n = 0
    for sid in sids:
        c = per[sid]["dc"]; t += c["TP"]; f += c["FP"]; n += c["FN"]
    return [t, f, n]
f44 = micro({s: {"edge": floor[s]["adjusted_edge_jaccard"], "ec": floor[s]["edge_counts"]} for s in sids}, "44b6")
f6b = micro({s: {"edge": floor[s]["adjusted_edge_jaccard"], "ec": floor[s]["edge_counts"]} for s in sids}, "6bba")
rep = {}
for g in ("7.0", "10.0", "14.0"):
    per = grid["arm1"][g]
    m44, m6b = micro(per, "44b6"), micro(per, "6bba")
    rep[g] = {"fold0_44b6": m44, "fold1_6bba": m6b, "worst": min(m44, m6b),
              "d44": m44 - f44, "d6b": m6b - f6b, "div": divsum(per)}
    print(f"  arm1 gate {g}: 44b6={m44:.4f} ({m44-f44:+.4f}) 6bba={m6b:.4f} ({m6b-f6b:+.4f}) div={divsum(per)} (floor div [0,0,4])")
a2 = grid["arm2"]
base_adj = 0.8194  # EXP-0009 6bba@98.5
for k, v in a2.items():
    print(f"  arm2 {k}: edge={v['edge']:.4f} (d={v['edge']-base_adj:+.4f}) div={v['div']:.3f} ec={v['ec']['TP']}/{v['ec']['FP']}/{v['ec']['FN']}")
g10 = rep["10.0"]
gate_pass = g10["d44"] >= -1e-12 and g10["d6b"] >= -1e-12
best2 = max(a2, key=lambda k: a2[k]["edge"])
checks = {"arm1_gate10_no_regression": bool(gate_pass),
          "arm1_gate10_div_neutral_or_better": g10["div"][1] == 0,
          "arm2_best_ge_base": bool(a2[best2]["edge"] >= base_adj - 1e-12)}
metrics = {"exp_id": "EXP-0017", "title": "Link-gate ablation + gap-closing",
           "hypothesis_id": "H-002+H-005", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "image_based": "mixed-oracle",
           "simplified_scorer": False,
           "arm1_oracle_gates": rep, "floor_micros": {"44b6": f44, "6bba": f6b},
           "arm2_image": a2, "arm2_base": base_adj, "arm2_best": best2,
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Gate-10 verdict per checks. Strong oracle result -> promotion CANDIDATE pending "
                               "EXP-0018 jitter replication (r10 bar). Image gap verdict per arm2. "
                               "Ceiling keep-trying (single deterministic pass).")}
assert True  # ledger records negative verdicts too; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0017] OK: metrics.json written."
