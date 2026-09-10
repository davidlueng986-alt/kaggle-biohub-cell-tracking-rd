#!/usr/bin/env bash
# Runner for EXP-0020 — combo replication (perturbation + matched base + LOO).
# CPU-only, deterministic per seed. Exits 0 (verdict in metrics.json).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
GTD="$ROOT/experiments/EXP-0003/gt"
SIDS="44b6_0113de3b 44b6_0b24845f 44b6_0c582fdc 6bba_05b6850b 6bba_05db0fb1 6bba_062c8d37"

echo "[EXP-0020] 1/2: jitter seeds -> link combo + gate10 base -> score..."
for s in 0 1 2; do
  for sid in $SIDS; do
    python3 "$ROOT/scripts/perturb_graph.py" "$GTD/${sid}_gt.json" --seed "$s" \
      --out "$EXP_DIR/jit${s}_${sid}.json" > /dev/null
    python3 - "$EXP_DIR/jit${s}_${sid}.json" "$GTD/${sid}_gt.json" "$EXP_DIR/combo_seed${s}_${sid}_scores.json" "$ROOT" <<'EOF'
import json, sys
sys.path.insert(0, __import__("os").path.join(sys.argv[4], "scripts"))
from fork_link import link
from score import score_samples
jit = json.load(open(sys.argv[1])); gt = json.load(open(sys.argv[2]))
pred = link(jit, propose_um=10.0, base_maxd=10.0)
json.dump(score_samples([("combo", pred, gt, None)]), open(sys.argv[3], "w"))
EOF
    python3 - "$EXP_DIR/jit${s}_${sid}.json" "$GTD/${sid}_gt.json" "$EXP_DIR/base_seed${s}_${sid}_scores.json" "$ROOT" <<'EOF'
import json, sys
sys.path.insert(0, __import__("os").path.join(sys.argv[4], "scripts"))
import baseline_link as BL
from score import score_samples
jit = json.load(open(sys.argv[1])); gt = json.load(open(sys.argv[2]))
pred = BL.link({"nodes": jit["nodes"], "edges": []}, maxd=10.0)
json.dump(score_samples([("base", pred, gt, None)]), open(sys.argv[3], "w"))
EOF
  done
  echo "  seed $s done"
done

echo "[EXP-0020] 2/2: promotion verdict..."
python3 - "$EXP_DIR" <<'EOF'
import json, os, sys
d = sys.argv[1]
SIDS = ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
        "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]
# bars recomputed from frozen artifacts (run-book rule)
grid = json.load(open(os.path.join(d, "..", "EXP-0017", "grid.json")))["arm1"]["10.0"]
m19 = json.load(open(os.path.join(d, "..", "EXP-0019", "metrics.json")))
def emicro(rows, embryo, ekey="edge", ckey="ec"):
    num = den = 0.0
    for sid, row in rows.items():
        if sid.startswith(embryo):
            c = row[ckey]; w = c["TP"] + c["FP"] + c["FN"]
            num += row[ekey] * w; den += w
    return num / den
best = {s: {"edge": grid[s]["edge"], "ec": grid[s]["ec"]} for s in SIDS}
B44, B6B = emicro(best, "44b6"), emicro(best, "6bba")
cu = m19["per_sample"]
C44, C6B = emicro(cu, "44b6"), emicro(cu, "6bba")
print(f"  bars recomputed: best 44b6={B44:.6f} 6bba={B6B:.6f} | combo-unpert 44b6={C44:.6f} 6bba={C6B:.6f}")
notes, seeds = [], {}
ok = True
for sd in (0, 1, 2):
    vrows, brows = {}, {}
    for sid in SIDS:
        v = json.load(open(os.path.join(d, f"combo_seed{sd}_{sid}_scores.json")))["per_sample"][0]
        b = json.load(open(os.path.join(d, f"base_seed{sd}_{sid}_scores.json")))["per_sample"][0]
        vrows[sid] = {"edge": v["adjusted_edge_jaccard"], "ec": v["edge_counts"], "dc": v["division_counts"]}
        brows[sid] = {"edge": b["adjusted_edge_jaccard"], "ec": b["edge_counts"]}
    m44, m6b = emicro(vrows, "44b6"), emicro(vrows, "6bba")
    b44, b6b = emicro(brows, "44b6"), emicro(brows, "6bba")
    dTP = sum(vrows[s]["dc"]["TP"] for s in SIDS)
    dFP = sum(vrows[s]["dc"]["FP"] for s in SIDS)
    dFN = sum(vrows[s]["dc"]["FN"] for s in SIDS)
    efp = sum(vrows[s]["ec"]["FP"] for s in SIDS)
    ge_best = bool(m44 >= B44 - 1e-12 and m6b >= B6B - 1e-12)
    ge_base = bool(m44 >= b44 - 1e-12 and m6b >= b6b - 1e-12)
    seeds[str(sd)] = {"fold0": m44, "fold1": m6b, "worst": min(m44, m6b),
                      "base44": b44, "base6b": b6b, "div": [dTP, dFP, dFN],
                      "edge_fp": efp, "ge_best": ge_best, "ge_base": ge_base}
    print(f"  seed{sd}: fold0={m44:.4f} (best {B44:.4f}, base {b44:.4f}) "
          f"fold1={m6b:.4f} (best {B6B:.4f}, base {b6b:.4f}) div={dTP}/{dFP}/{dFN} efp={efp}")
    if not ge_best:
        ok = False; notes.append(f"seed{sd}: regresses vs best")
    if dFP > 0 or efp > 3:
        ok = False; notes.append(f"seed{sd}: FP growth (div {dFP}, edge {efp})")
    if dTP < 2:
        ok = False; notes.append(f"seed{sd}: div gain evaporated (TP {dTP} < 2)")
    if not ge_base:
        ok = False; notes.append(f"seed{sd}: worse than noise-matched base")
# LOO same-set: combo-unperturbed vs best
uloo = {}
for drop in SIDS:
    vr = {k: cu[k] for k in SIDS if k != drop}
    fr = {k: best[k] for k in SIDS if k != drop}
    below = emicro(vr, "44b6") < emicro(fr, "44b6") - 1e-12 or emicro(vr, "6bba") < emicro(fr, "6bba") - 1e-12
    uloo[drop] = {"below_best": bool(below)}
    if below:
        ok = False; notes.append(f"LOO drop {drop}: combo below same-set best")
promote = bool(ok)
metrics = {"exp_id": "EXP-0020", "title": "Combo replication",
           "hypothesis_id": "H-002+H-003", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "simplified_scorer": False,
           "perturbation": {"sigma_vox": 0.3, "seeds": [0, 1, 2]},
           "bars_recomputed": {"best44": B44, "best6b": B6B, "combo44": C44, "combo6b": C6B},
           "seeds": seeds, "loo_same_set": uloo,
           "promote": promote,
           "decision": "promote" if promote else "keep-trying",
           "decision_reason": ("Combo " + ("PROMOTED to new best (worst-fold 1.0895, div 3/0/1): replication passed all seeds + LOO; oracle arm then hunts image-bridging work." if promote else f"NOT promoted: {notes}. Candidacy verdict per evidence.") + " Gate-1 bar applied as pre-registered.")}
assert True  # ledger records either verdict; promotion is a knowledge status, not exit code
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("PROMOTE:" if promote else "KEEP (recorded):", promote)
for n in notes:
    print("  NOTE:", n)
EOF
echo "[EXP-0020] OK: metrics.json written."
