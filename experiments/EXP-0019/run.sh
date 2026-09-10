#!/usr/bin/env bash
# Runner for EXP-0019 — gate-10 + r10 combination vs new best.
# CPU-only, deterministic. Exits 0 (verdict in metrics.json even if negative).
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"
SIDS="44b6_0113de3b 44b6_0b24845f 44b6_0c582fdc 6bba_05b6850b 6bba_05db0fb1 6bba_062c8d37"

echo "[EXP-0019] 1/2: combo links + scores..."
for sid in $SIDS; do
  python3 - "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" "$EXP_DIR/${sid}_pred.json" <<'EOF'
import json, sys
sys.path.insert(0, "scripts")
from fork_link import link
gt = json.load(open(sys.argv[1]))
pred = link(gt, propose_um=10.0, base_maxd=10.0)
json.dump(pred, open(sys.argv[2], "w"))
print(f"  wrote {sys.argv[2]}: edges={len(pred['edges'])} fork_extra={pred['n_fork_extra']}")
EOF
  python3 "$ROOT/scripts/score.py" \
    --pred "$EXP_DIR/${sid}_pred.json" \
    --gt "$ROOT/experiments/EXP-0003/gt/${sid}_gt.json" \
    --out "$EXP_DIR/${sid}_scores.json" > /dev/null
done

echo "[EXP-0019] 2/2: verdict vs new best..."
python3 - "$EXP_DIR" $SIDS <<'EOF'
import json, os, sys
d = sys.argv[1]; sids = sys.argv[2:]
# best = recomputed gate-10 micros from frozen EXP-0017 grid (never rounded literals)
grid = json.load(open(os.path.join(d, "..", "EXP-0017", "grid.json")))["arm1"]["10.0"]
B44 = sum(grid[s]["edge"] * (grid[s]["ec"]["TP"] + grid[s]["ec"]["FP"] + grid[s]["ec"]["FN"]) for s in sids if s.startswith("44b6")) / sum(grid[s]["ec"]["TP"] + grid[s]["ec"]["FP"] + grid[s]["ec"]["FN"] for s in sids if s.startswith("44b6"))
B6B = sum(grid[s]["edge"] * (grid[s]["ec"]["TP"] + grid[s]["ec"]["FP"] + grid[s]["ec"]["FN"]) for s in sids if s.startswith("6bba")) / sum(grid[s]["ec"]["TP"] + grid[s]["ec"]["FP"] + grid[s]["ec"]["FN"] for s in sids if s.startswith("6bba"))
print(f"  best recomputed: 44b6={B44:.6f} 6bba={B6B:.6f}")
per = {}
for sid in sids:
    s = json.load(open(os.path.join(d, f"{sid}_scores.json")))["per_sample"][0]
    p = json.load(open(os.path.join(d, f"{sid}_pred.json")))
    per[sid] = {"edge": s["adjusted_edge_jaccard"], "div": s["division_jaccard"],
                "score": s["score"], "ec": s["edge_counts"], "dc": s["division_counts"],
                "extra": p.get("n_fork_extra", 0)}
    print(f"  {sid}: edge={s['adjusted_edge_jaccard']:.4f} div={s['division_jaccard']:.3f} "
          f"ec={s['edge_counts']['TP']}/{s['edge_counts']['FP']}/{s['edge_counts']['FN']} "
          f"dc={s['division_counts']['TP']}/{s['division_counts']['FP']}/{s['division_counts']['FN']} extra={p.get('n_fork_extra', 0)}")
def micro(embryo):
    num = den = 0.0
    for sid in sids:
        if sid.startswith(embryo):
            c = per[sid]["ec"]; w = c["TP"] + c["FP"] + c["FN"]
            num += per[sid]["edge"] * w; den += w
    return num / den
m44, m6b = micro("44b6"), micro("6bba")
dTP = sum(per[s]["dc"]["TP"] for s in sids)
dFP = sum(per[s]["dc"]["FP"] for s in sids)
dFN = sum(per[s]["dc"]["FN"] for s in sids)
forks44 = sum(per[s]["extra"] for s in sids if s.startswith("44b6"))
checks = {"div_gain": dTP >= 1 and dFP <= 1,
          "no_regress_44b6": m44 >= B44 - 1e-12,
          "no_regress_6bba": m6b >= B6B - 1e-12,
          "no_44b6_forks": forks44 == 0}
print(f"  micro44={m44:.4f} (best {B44}) micro6b={m6b:.4f} (best {B6B}) "
      f"div={dTP}/{dFP}/{dFN} forks44={forks44}")
metrics = {"exp_id": "EXP-0019", "title": "Gate-10 + r10-fork combination",
           "hypothesis_id": "H-002+H-003", "protocol_version": "1.1",
           "dry_run": False, "real_data": True, "simplified_scorer": False,
           "combo": {"propose_um": 10.0, "base_maxd": 10.0},
           "per_sample": per,
           "micros": {"44b6": m44, "6bba": m6b, "worst": min(m44, m6b)},
           "best": {"44b6": B44, "6bba": B6B},
           "div_sums": {"TP": dTP, "FP": dFP, "FN": dFN},
           "checks": checks, "all_checks_pass": all(checks.values()),
           "decision": "keep-trying",
           "decision_reason": ("Combo verdict per checks. Pass -> promotion CANDIDATE pending EXP-0020 replication "
                               "(same bar as gate-10). Fail -> park combo, r10 stays standalone ensemble-candidate. "
                               "Ceiling keep-trying (single deterministic pass).")}
assert True  # ledger records either verdict; verdict in checks
json.dump(metrics, open(os.path.join(d, "metrics.json"), "w"), indent=2)
print("checks:", checks)
for k, v in checks.items():
    if not v: print("FALSIFIED (recorded):", k)
EOF
echo "[EXP-0019] OK: metrics.json written."
