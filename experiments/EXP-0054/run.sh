#!/usr/bin/env bash
# EXP-0054 — GT-free count-target analysis (ANALYSIS ONLY, frozen artifacts).
# Recomputes the (T_ratio, det/frame, edge_raw, edge_adj) table from frozen
# metrics.json files, bins edge_raw by T_ratio, hand-rolls two Spearman rank
# correlations, locates each sample's best operating point, and writes
# metrics.json. No detection/linking, no recomputation of scores.
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

python3 - "$ROOT" "$EXP_DIR" <<'EOF'
import json, sys
from pathlib import Path

ROOT = Path(sys.argv[1]); EXP_DIR = Path(sys.argv[2])

def load(exp):
    with open(ROOT / "experiments" / exp / "metrics.json") as f:
        return json.load(f)

m08, m09, m11, m12 = load("EXP-0008"), load("EXP-0009"), load("EXP-0011"), load("EXP-0012")
m21, m39, m40, m43, m44 = load("EXP-0021"), load("EXP-0039"), load("EXP-0040"), load("EXP-0043"), load("EXP-0044")

# Unique detection-operating rows: (sample, op, source, T_ratio, det_f, raw, adj).
# EXP-0010 combo duplicates EXP-0009 operating points (no independent T_ratio) -> ledger only.
# EXP-0008 full_video_p99 n_det_total copies window-probe per-frame means (140.1/48.4),
#   inconsistent with EXP-0021 full-video totals for identical edge counts -> excluded, ledger only.
# EXP-0044 fork arm is a linker-only variant at identical counts -> mechanism note only.
rows = [
    ("44b6_0113de3b", "@99.0",      "EXP-0021", 0.6197631527858668, 159.62, 0.9038461538461539, 0.938213715036662),
    ("44b6_0113de3b", "@98.5",      "EXP-0009", 0.7315860997864493, 188.42, 0.9038461538461539, 0.9281066409808402),
    ("44b6_0b24845f", "@99.0-bar",  "EXP-0021", 0.3961579509071505, 129.92, 0.09803921568627451, 0.10395923577542009),
    ("44b6_0b24845f", "@96.0",      "EXP-0040", 0.7016008537886873, 230.09, 0.18181818181818182, 0.18724362084020568),
    ("44b6_0c582fdc", "@99.0-bar",  "EXP-0021", 0.45707847485513986, 127.79, 0.09090909090909091, 0.09584474113768054),
    ("44b6_0c582fdc", "@96.0",      "EXP-0040", 0.559482080263252,  156.42, 0.1794871794871795, 0.18739391137989034),
    ("6bba_05b6850b", "@98.5",      "EXP-0009", 0.7423766111285759, 47.23,  0.7988571428571428, 0.8194375712938429),
    ("6bba_05b6850b", "@98.0",      "EXP-0011", 0.7717698836843759, 49.10,  0.7882623705408516, 0.8062528917924284),
    ("6bba_05b6850b", "@98.0+split","EXP-0012", 0.9858535051870481, 62.72,  0.7077986179664363, 0.708799904914204),
    ("6bba_05db0fb1", "@98.5-bar",  "EXP-0021", 0.3748997134670487, 261.68, 0.19686274509803922, 0.209168640934884),
    ("6bba_05db0fb1", "@96.0",      "EXP-0039", 0.6015329512893983, 419.87, 0.4637247569184742, 0.4822026604488088),
    ("6bba_062c8d37", "@98.5-bar",  "EXP-0021", 0.8361525704809287, 50.42,  0.8507625272331155, 0.8647020525549449),
    ("6bba_062c8d37", "@96.0",      "EXP-0043", 0.8922056384742952, 53.80,  0.7776572668112798, 0.7860399736674544),
]
# Cross-check harvested values against frozen sources (fail loudly on drift).
checks = [
    (m09["rows"]["44b6_0113de3b"], ("T_ratio", 0.7315860997864493), ("edge_raw", 0.9038461538461539)),
    (m09["rows"]["6bba_05b6850b"], ("T_ratio", 0.7423766111285759), ("edge_raw", 0.7988571428571428)),
    (m11["row"], ("T_ratio", 0.7717698836843759), ("edge_raw", 0.7882623705408516)),
    (m12["row"], ("T_ratio", 0.9858535051870481), ("edge_raw", 0.7077986179664363)),
    (m39["comparison"]["@96.0"], ("T_ratio", 0.6015329512893983), ("raw", 0.4637247569184742)),
    (m40["per_sample"]["44b6_0b24845f"]["@96.0"], ("T_ratio", 0.7016008537886873), ("raw", 0.18181818181818182)),
    (m40["per_sample"]["44b6_0c582fdc"]["@96.0"], ("T_ratio", 0.559482080263252), ("raw", 0.1794871794871795)),
    (m43["comparison"]["@96.0"], ("T_ratio", 0.8922056384742952), ("raw", 0.7776572668112798)),
]
for src, (k1, v1), (k2, v2) in checks:
    assert abs(src[k1] - v1) < 1e-12, (k1, src[k1], v1)
    assert abs(src[k2] - v2) < 1e-12, (k2, src[k2], v2)
for s, d in m21["per_sample"].items():
    match = [r for r in rows if r[0] == s and r[2] == "EXP-0021"]
    for (s2, op, src, tr, df, raw, adj) in match:
        assert abs(d["T_ratio"] - tr) < 1e-12 and abs(d["raw"] - raw) < 1e-12, s2

def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs); i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r

def spearman(xs, ys):
    n = len(xs); rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx); vy = sum((b - my) ** 2 for b in ry)
    return cov / (vx * vy) ** 0.5

TR  = [r[3] for r in rows]; DET = [r[4] for r in rows]; RAW = [r[5] for r in rows]
sp_tr, sp_det = spearman(TR, RAW), spearman(DET, RAW)

bins = {"0-0.5": [], "0.5-0.8": [], "0.8-1.0": [], "1.0+": []}
for t, raw in zip(TR, RAW):
    bins["0-0.5" if t < 0.5 else "0.5-0.8" if t < 0.8 else "0.8-1.0" if t < 1.0 else "1.0+"].append(raw)
binned = {k: {"n": len(v), "mean_raw": (sum(v) / len(v) if v else None)} for k, v in bins.items()}

by_sample = {}
for s, op, src, tr, df, raw, adj in rows:
    by_sample.setdefault(s, []).append({"op": op, "src": src, "T_ratio": tr, "det_f": df, "raw": raw, "adj": adj})
best, deltas = {}, {}
for s, pts in by_sample.items():
    b = max(pts, key=lambda p: p["raw"]); best[s] = b
    lo = min(pts, key=lambda p: p["T_ratio"]); hi = max(pts, key=lambda p: p["T_ratio"])
    deltas[s] = {"dT": hi["T_ratio"] - lo["T_ratio"], "draw": hi["raw"] - lo["raw"],
                 "lo_op": lo["op"], "hi_op": hi["op"], "n_ops": len(pts)}

out = {
    "exp_id": "EXP-0054",
    "title": "GT-free count target analysis (T_ratio vs edge)",
    "hypothesis_id": "H-002/H-004",
    "status": "done",
    "sources": ["EXP-0008", "EXP-0009", "EXP-0010", "EXP-0011", "EXP-0012",
                "EXP-0021", "EXP-0039", "EXP-0040", "EXP-0043", "EXP-0044"],
    "n_unique_rows": len(rows),
    "table": [{"sample": s, "op": op, "src": src, "T_ratio": tr, "det_f": df,
               "edge_raw": raw, "edge_adj": adj} for s, op, src, tr, df, raw, adj in rows],
    "excluded_ledger": [
        "EXP-0008 full_video_p99 rows: n_det_total copies window-probe per-frame means; T_ratio underivable; edge values kept as reference only",
        "EXP-0010 combo rows: duplicate EXP-0009 operating points, no independent T_ratio",
        "EXP-0021/M39/M40/M43 rescore bars: verified bit-identical duplicates of EXP-0009/EXP-0021 arms (rescore_match_ledger true)",
        "EXP-0044 fork_r10 arm: linker-only variant at identical counts (raw -0.0014, div FP +35, adj -0.0015); FP-mechanism note, not a count row",
    ],
    "binned_edge_raw_by_T_ratio": binned,
    "spearman_T_ratio_vs_raw": round(sp_tr, 4),
    "spearman_det_f_vs_raw": round(sp_det, 4),
    "within_sample": {"best_by_raw": best, "lowT_to_highT": deltas},
    "best_T_ratio_span": [min(b["T_ratio"] for b in best.values()), max(b["T_ratio"] for b in best.values())],
    "best_det_f_span": [min(b["det_f"] for b in best.values()), max(b["det_f"] for b in best.values())],
    "verdict": "NOT_EXISTS",
    "verdict_reason": (
        "No GT-free count target beats per-sample tuning. (1) Best-T_ratio spans 0.56-0.84 with 3/6 "
        "samples still rising at their max-T arm (peaks uncaptured); best-det/f spans 47-420 (9x), so no "
        "fixed detection/video prior is jointly near-optimal. (2) Pooled det/f predicts edge WORSE "
        "(Spearman -0.25) than T_ratio (+0.59), and within-sample they are exactly proportional, so det/f "
        "adds nothing once per-sample scale is known. (3) T_ratio itself needs T_true from GT .geff metadata "
        "(docs/COMPETITION.md:28,55), unobservable on hidden test: a T_ratio interval is circular as a GT-free rule. "
        "Hidden-test operating discipline stays OPEN; embryo caveat: all rows from 2 train embryos, hidden is "
        "embryo-disjoint, and per-embryo levels already failed on new samples (EXP-0021/EXP-0043)."
    ),
}
with open(EXP_DIR / "metrics.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"[EXP-0054] rows={len(rows)} bins={ {k: v['n'] for k, v in binned.items()} } "
      f"spearman_T={sp_tr:.4f} spearman_det={sp_det:.4f} verdict=NOT_EXISTS")
EOF
echo "[EXP-0054] metrics.json written."