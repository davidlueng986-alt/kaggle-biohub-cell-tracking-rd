#!/usr/bin/env python3
"""EXP-0024 sweep: per-sample threshold map (detection/recall-only rung).

For each failing sample x pct: run frozen DoG detection (scripts/dog_detect.detect,
sigmas (1,3,3)/(1.6,5,5), min-size 50 — same code path as the CLI) over window
t=20..29, match vs GT nodes at same t via scripts/score.match_nodes, record
recall (matched GT / total GT over window) + mean det/frame + mean s/frame.

CPU-only, deterministic (fixed pcts, no randomness). Writes metrics.json.
"""
import json
import os
import sys
import time

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import zarr  # noqa: E402
from dog_detect import detect, SIG_SMALL, SIG_LARGE  # noqa: E402
from score import match_nodes  # noqa: E402

SAMPLES = ["44b6_0b24845f", "44b6_0c582fdc", "6bba_05db0fb1"]
PCTS = [97.5, 98.0, 98.5, 99.0, 99.5]
T0, T1 = 20, 29  # inclusive window (10 frames)
MIN_SIZE = 50

assert tuple(SIG_SMALL) == (1.0, 3.0, 3.0), "frozen sigma-small drifted"
assert tuple(SIG_LARGE) == (1.6, 5.0, 5.0), "frozen sigma-large drifted"


def main():
    t_start = time.time()
    table = {}  # sid -> pct_str -> {recall, det_per_frame, s_per_frame, ...}
    for sid in SAMPLES:
        gt = json.load(open(os.path.join(
            ROOT, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
        gt_win = [n for n in gt["nodes"] if T0 <= int(n["t"]) <= T1]
        n_gt = len(gt_win)
        assert n_gt > 0, f"no GT in window for {sid}"
        group = zarr.open_group(os.path.join(ROOT, "data/train", f"{sid}.zarr"),
                                mode="r")["0"]
        table[sid] = {}
        for pct in PCTS:
            pred_nodes, det_counts, elapsed = [], [], []
            gid = 0
            for t in range(T0, T1 + 1):
                vol = group[t]
                nodes, params = detect(vol, pct=pct, min_size=MIN_SIZE,
                                       sig_small=tuple(SIG_SMALL),
                                       sig_large=tuple(SIG_LARGE))
                elapsed.append(params["elapsed_s"])
                det_counts.append(len(nodes))
                for (z, y, x, _sp, _pa) in nodes:
                    gid += 1
                    pred_nodes.append({"id": gid, "t": t, "z": z, "y": y,
                                       "x": x})
            _, g2p = match_nodes(pred_nodes, gt_win)
            recall = len(g2p) / n_gt
            table[sid][str(pct)] = {
                "recall": round(recall, 4),
                "matched": len(g2p),
                "n_gt": n_gt,
                "det_per_frame": round(sum(det_counts) / len(det_counts), 1),
                "total_det": sum(det_counts),
                "s_per_frame": round(sum(elapsed) / len(elapsed), 2),
            }
            r = table[sid][str(pct)]
            print(f"  {sid} @ {pct}: recall={r['recall']:.4f} "
                  f"({r['matched']}/{r['n_gt']}) det/f={r['det_per_frame']} "
                  f"s/f={r['s_per_frame']}", flush=True)

    best = {}
    for sid in SAMPLES:
        rows = [(float(p), v) for p, v in table[sid].items()]
        rows.sort(key=lambda kv: (-kv[1]["recall"], kv[1]["det_per_frame"],
                                  kv[0]))
        bp, bv = rows[0]
        best[sid] = {"pct": bp, "recall": bv["recall"],
                     "det_per_frame": bv["det_per_frame"],
                     "s_per_frame": bv["s_per_frame"]}
    rescued = all(v["recall"] >= 0.90 for v in best.values())
    dark = sorted(s for s, v in best.items() if v["recall"] < 0.90)
    verdict = "TRANSFER-RESCUED" if rescued else "NOT-RESCUED"
    metrics = {
        "exp_id": "EXP-0024",
        "title": "Per-sample threshold map",
        "status": "done",
        "protocol_version": "1.1",
        "real_data": True,
        "image_based": True,
        "simplified_scorer": False,
        "scope": "detection/recall-only (no edges; edge readout deferred to "
                 "full-video follow-up once a level is selected)",
        "window": {"t0": T0, "t1": T1, "n_frames": T1 - T0 + 1},
        "pcts": PCTS,
        "detector": {"sig_small": list(SIG_SMALL),
                     "sig_large": list(SIG_LARGE), "min_size": MIN_SIZE,
                     "thr_mode": "percentile"},
        "per_sample_pct": table,
        "best": best,
        "threshold": 0.90,
        "verdict": verdict,
        "dark_samples": dark,
        "wall_s": round(time.time() - t_start, 1),
    }
    with open(os.path.join(EXP_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[EXP-0024] verdict={verdict} dark={dark} "
          f"({metrics['wall_s']}s wall)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
