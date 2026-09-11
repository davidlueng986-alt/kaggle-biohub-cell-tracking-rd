#!/usr/bin/env bash
# Runner for EXP-0051 — GT-motion regime test (analysis-only, no detection/linking).
# CPU-only, deterministic. Recomputes GT-motion stats from EXP-0003 GT + frozen
# gate deltas (EXP-0050 metrics.json + EXP-0017 grid.json), hand-rolled Spearman,
# and rewrites experiments/EXP-0051/metrics.json. Exits 0 (verdict in JSON).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0051] GT-motion regime test (read GT + frozen artifacts, no linking)..."
python3 - "$EXP_DIR" "$ROOT" <<'EOF'
import json, math, os, sys
d, root = sys.argv[1], sys.argv[2]
try:
    import numpy as np
except ImportError:
    print("EXP-0051 needs numpy", file=sys.stderr); sys.exit(2)
VOX = (1.625, 0.40625, 0.40625)
SIDS = ["44b6_0113de3b","44b6_0b24845f","44b6_0c582fdc",
        "6bba_05b6850b","6bba_05db0fb1","6bba_062c8d37"]

def ranks(vals):
    """Average-rank ties, rank 1 = largest value. Deterministic."""
    idx = sorted(range(len(vals)), key=lambda i: vals[i], reverse=True)
    r = [0.0]*len(vals); i = 0
    while i < len(idx):
        j = i
        while j+1 < len(idx) and vals[idx[j+1]] == vals[idx[i]]:
            j += 1
        avg = (i+1 + j+1)/2.0
        for k in range(i, j+1):
            r[idx[k]] = avg
        i = j+1
    return r

def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    n = len(x)
    mx = sum(rx)/n; my = sum(ry)/n
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    dx = sum((a-mx)**2 for a in rx); dy = sum((b-my)**2 for b in ry)
    den = math.sqrt(dx*dy)
    return (num/den if den else 0.0), rx, ry

stats = {}
for sid in SIDS:
    g = json.load(open(os.path.join(root, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
    byid = {n["id"]: n for n in g["nodes"]}
    assert g.get("voxel_size_um", [1.625,0.40625,0.40625]) == [1.625,0.40625,0.40625], sid
    disp = []
    for u, v in g["edges"]:
        a, b = byid[u], byid[v]
        assert b["t"]-a["t"] == 1, f"{sid} non-dt1 edge"
        dz=(a["z"]-b["z"])*VOX[0]; dy=(a["y"]-b["y"])*VOX[1]; dx=(a["x"]-b["x"])*VOX[2]
        disp.append(math.sqrt(dz*dz+dy*dy+dx*dx))
    arr = np.array(disp)
    occ = len(set(n["t"] for n in g["nodes"]))
    stats[sid] = {
        "n_nodes": len(byid), "n_edges": len(disp),
        "n_occupied_frames": occ,
        "density_nodes_per_frame": len(byid)/occ,
        "frac_7_10": float(np.mean((arr>7)&(arr<=10))),
        "n_fast_7_10": int(np.sum((arr>7)&(arr<=10))),
        "frac_gt7": float(np.mean(arr>7)), "frac_gt10": float(np.mean(arr>10)),
        "median_um": float(np.median(arr)), "p90_um": float(np.percentile(arr,90)),
        "max_um": float(np.max(arr)),
    }
    s = stats[sid]
    print(f"  {sid}: edges={s['n_edges']} nodes={s['n_nodes']} occ={occ} "
          f"dens={s['density_nodes_per_frame']:.3f} frac710={s['frac_7_10']:.6f} "
          f"({s['n_fast_7_10']}/{s['n_edges']}) med={s['median_um']:.4f} "
          f"p90={s['p90_um']:.4f} max={s['max_um']:.4f}", flush=True)

m50 = json.load(open(os.path.join(root, "experiments/EXP-0050/metrics.json")))
img_adv = {sid: -m50["per_sample"][sid]["delta_adj_g7_minus_g10"] for sid in SIDS}
grid = json.load(open(os.path.join(root, "experiments/EXP-0017/grid.json")))
oracle_adv = {sid: grid["arm1"]["10.0"][sid]["edge"]-grid["arm1"]["7.0"][sid]["edge"] for sid in SIDS}
print("  IMAGE g10-g7 adj:", {k: round(v,6) for k,v in img_adv.items()}, flush=True)
print("  ORACLE g10-g7 adj:", {k: round(v,6) for k,v in oracle_adv.items()}, flush=True)

fast  = [stats[s]["frac_7_10"] for s in SIDS]
dens  = [stats[s]["density_nodes_per_frame"] for s in SIDS]
p90   = [stats[s]["p90_um"] for s in SIDS]
img   = [img_adv[s] for s in SIDS]
orac  = [oracle_adv[s] for s in SIDS]
rho_img_fast, rx_f, ry_img = spearman(fast, img)
rho_img_dens, rx_d, ry_img2 = spearman(dens, img)
rho_or_fast, _, ry_or = spearman(fast, orac)
rho_or_p90, _, _ = spearman(p90, orac)
assert ry_img == ry_img2
print(f"  rho fast-vs-IMAGE={rho_img_fast:.4f} dens-vs-IMAGE={rho_img_dens:.4f} "
      f"fast-vs-ORACLE={rho_or_fast:.4f} p90-vs-ORACLE={rho_or_p90:.4f}", flush=True)
print(f"  fast ranks={rx_f} image-adv ranks={ry_img} oracle-adv ranks={ry_or}", flush=True)

verdict = "STRONG-MECHANISM" if rho_img_fast >= 0.8 else "WEAK"
out = {
  "exp_id": "EXP-0051",
  "title": "GT-motion regime test for gate-10 advantage (analysis-only)",
  "protocol_version": "1.1", "scorer_version": "1.1.0",
  "analysis_only": True, "no_detection": True, "no_linking": True,
  "voxel_size_um": list(VOX),
  "gt_stats": stats,
  "gate_deltas_g10_minus_g7_adj": {
     "image_from_EXP0050": img_adv, "oracle_from_EXP0017_grid": oracle_adv},
  "rank_table": {
     "order": SIDS,
     "fast_frac_rank_desc": rx_f, "density_rank_desc": rx_d,
     "image_adv_rank_desc": ry_img, "oracle_adv_rank_desc": ry_or},
  "spearman": {
     "fast_vs_image_adv": rho_img_fast,
     "density_vs_image_adv": rho_img_dens,
     "fast_vs_oracle_adv": rho_or_fast,
     "p90_vs_oracle_adv": rho_or_p90},
  "verdict": verdict,
  "verdict_rule": "STRONG-MECHANISM iff fast_vs_image_adv rho>=0.8 else WEAK",
  "decision": "keep uniform gate-7; do not pursue per-regime gate" if verdict=="WEAK"
              else "per-regime gate has principled selector; future gated rung GO",
}
json.dump(out, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print(f"[EXP-0051] verdict={verdict} (fast-vs-IMAGE rho={rho_img_fast:.4f})")
EOF
echo "[EXP-0051] done. see metrics.json"
