#!/usr/bin/env python3
"""EXP-0034 transfer test: per-sample-best window levels -> full video.

For each of 3 samples at its EXP-0024 best pct: detect all 100 frames with
frozen DoG (scripts/dog_detect.detect, same code path as CLI defaults),
global gid re-id per video, link with baseline_link, score full video via
the real score.py CLI (true T_true), plus in-process window-slice (t20-29)
linked score (window-implied edge) and micro recalls. Writes metrics.json.

CPU-only, deterministic (no randomness). Outputs stay in EXP-0034/.
"""
import json
import os
import subprocess
import sys
import time

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import zarr  # noqa: E402
from dog_detect import detect, SIG_SMALL, SIG_LARGE  # noqa: E402
import baseline_link as BL  # noqa: E402
from score import match_nodes, score_samples, PROTOCOL_VERSION, SCORER_VERSION  # noqa: E402

SAMPLES = {
    "44b6_0b24845f": 98.5,
    "44b6_0c582fdc": 97.5,
    "6bba_05db0fb1": 97.5,
}
WINDOW_REF_RECALL = {
    "44b6_0b24845f": 0.8,
    "44b6_0c582fdc": 0.5,
    "6bba_05db0fb1": 0.4056,
}
T0, T1 = 20, 29  # EXP-0024 window, inclusive
MIN_SIZE = 50
RECALL_TOL = 0.10
EDGE_TOL = 0.10

assert tuple(SIG_SMALL) == (1.0, 3.0, 3.0), "frozen sigma-small drifted"
assert tuple(SIG_LARGE) == (1.6, 5.0, 5.0), "frozen sigma-large drifted"


def main():
    t_start = time.time()
    per_sample = {}
    for sid, pct in SAMPLES.items():
        t_sid = time.time()
        gt = json.load(open(os.path.join(
            ROOT, "experiments/EXP-0003/gt", f"{sid}_gt.json")))
        group = zarr.open_group(
            os.path.join(ROOT, "data/train", f"{sid}.zarr"), mode="r")["0"]
        assert group.shape[0] == 100, f"{sid}: expected 100 frames"

        nodes, gid = [], 0
        det_counts, elapsed = [], []
        for t in range(100):
            vol = group[t]
            found, params = detect(vol, pct=pct, min_size=MIN_SIZE,
                                   sig_small=tuple(SIG_SMALL),
                                   sig_large=tuple(SIG_LARGE))
            elapsed.append(params["elapsed_s"])
            det_counts.append(len(found))
            for (z, y, x, _sp, _pa) in found:
                gid += 1
                nodes.append({"id": gid, "t": t, "z": z, "y": y, "x": x})
        print(f"  {sid} @ {pct}: det/f={gid / 100:.1f} "
              f"s/f={sum(elapsed) / len(elapsed):.2f}", flush=True)

        # full-video link + score via real score.py CLI (true T_true)
        full_pred = BL.link({"nodes": nodes, "edges": []})
        pred_path = os.path.join(EXP_DIR, f"{sid}_pred.json")
        json.dump(full_pred, open(pred_path, "w"))
        gt_path = os.path.join(ROOT, "experiments/EXP-0003/gt",
                               f"{sid}_gt.json")
        scores_path = os.path.join(EXP_DIR, f"{sid}_scores.json")
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts/score.py"),
             "--pred", pred_path, "--gt", gt_path, "--out", scores_path],
            check=True, capture_output=True, text=True)
        full_cli = json.load(open(scores_path))["per_sample"][0]
        full_adj = full_cli["adjusted_edge_jaccard"]
        full_raw = full_cli["edge_jaccard_raw"]

        # full-video micro recall (same definition as EXP-0024 window recall)
        _p2g, g2p_full = match_nodes(nodes, gt["nodes"])
        full_rec = len(g2p_full) / len(gt["nodes"])

        # window slice of SAME detections: recomputed recall (determinism
        # check) + linked window-implied edge (true full-video T_true)
        win_nodes = [n for n in nodes if T0 <= n["t"] <= T1]
        win_gt_nodes = [n for n in gt["nodes"] if T0 <= int(n["t"]) <= T1]
        _p2g_w, g2p_w = match_nodes(win_nodes, win_gt_nodes)
        win_rec_recomp = len(g2p_w) / len(win_gt_nodes)
        win_ids = {n["id"] for n in win_gt_nodes}
        win_gt = {"nodes": win_gt_nodes,
                  "edges": [e for e in gt.get("edges", [])
                            if e[0] in win_ids and e[1] in win_ids],
                  "T_true": gt.get("T_true"),
                  "voxel_size_um": gt.get("voxel_size_um")}
        win_pred = BL.link({"nodes": [dict(n) for n in win_nodes],
                            "edges": []})
        win_s = score_samples([(sid, win_pred, win_gt, None)])[ 
            "per_sample"][0]
        win_adj = win_s["adjusted_edge_jaccard"]

        win_ref = WINDOW_REF_RECALL[sid]
        d_rec = full_rec - win_ref
        d_edge = full_adj - win_adj
        rec_ok = abs(d_rec) <= RECALL_TOL
        edge_ok = abs(d_edge) <= EDGE_TOL
        verdict = "TRANSFER-HOLDS" if (rec_ok and edge_ok) else "BREAKS"
        direction = []
        if not rec_ok:
            direction.append("recall_" + ("down" if d_rec < 0 else "up"))
        if not edge_ok:
            direction.append("edge_" + ("down" if d_edge < 0 else "up"))

        per_sample[sid] = {
            "pct": pct,
            "window_recall_ref": win_ref,
            "window_recall_recomputed": round(win_rec_recomp, 4),
            "full_recall": round(full_rec, 4),
            "d_recall_full_minus_window": round(d_rec, 4),
            "recall_within_0.10": rec_ok,
            "window_slice_edge_adj": round(win_adj, 4),
            "window_slice_edge_raw": round(win_s["edge_jaccard_raw"], 4),
            "full_edge_adj": round(full_adj, 4),
            "full_edge_raw": round(full_raw, 4),
            "d_edge_full_minus_window": round(d_edge, 4),
            "edge_within_0.10": edge_ok,
            "full_minus_window_recall_gap_for_transparency": round(
                full_adj - win_ref, 4),
            "full_division_jaccard": full_cli["division_jaccard"],
            "full_score": full_cli["score"],
            "full_edge_counts": full_cli["edge_counts"],
            "full_division_counts": full_cli["division_counts"],
            "full_T_pred": full_cli["T_pred"],
            "full_T_true": full_cli["T_true"],
            "window_edge_counts": win_s["edge_counts"],
            "n_gt_full": len(gt["nodes"]),
            "n_gt_window": len(win_gt_nodes),
            "det_per_frame": round(gid / 100, 1),
            "total_det": gid,
            "s_per_frame": round(sum(elapsed) / len(elapsed), 2),
            "verdict": verdict,
            "direction": direction if direction else ["none"],
            "link_assign": full_pred.get("assign"),
        }
        print(f"  {sid}: win_rec={win_ref:.4f} full_rec={full_rec:.4f} "
              f"(d={d_rec:+.4f}) win_adj={win_adj:.4f} "
              f"full_adj={full_adj:.4f} (d={d_edge:+.4f}) -> {verdict}",
              flush=True)

    n_holds = sum(1 for v in per_sample.values()
                  if v["verdict"] == "TRANSFER-HOLDS")
    overall = ("GO" if n_holds == 3 else "STOP")
    metrics = {
        "exp_id": "EXP-0034",
        "title": "Per-sample-best transfer test",
        "status": "done",
        "protocol_version": PROTOCOL_VERSION,
        "scorer_version": SCORER_VERSION,
        "real_data": True,
        "image_based": True,
        "simplified_scorer": False,
        "window": {"t0": T0, "t1": T1},
        "levels": SAMPLES,
        "window_ref": WINDOW_REF_RECALL,
        "criteria": {"recall_tol": RECALL_TOL, "edge_tol": EDGE_TOL,
                     "rule": "HOLDS iff |d_recall|<=0.10 AND |d_edge|<=0.10; "
                             "GO iff 3/3 HOLDS else STOP"},
        "per_sample": per_sample,
        "n_holds": n_holds,
        "overall": overall,
        "overall_reason": (
            "per-sample window-selected levels viable; recommend EXP-0035 "
            "full-subset policy" if overall == "GO" else
            "window selection does not transfer; per-video calibration must "
            "be full-video or learned"),
        "detector": {"sig_small": list(SIG_SMALL),
                     "sig_large": list(SIG_LARGE), "min_size": MIN_SIZE,
                     "thr_mode": "percentile"},
        "wall_s": round(time.time() - t_start, 1),
    }
    with open(os.path.join(EXP_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[EXP-0034] holds={n_holds}/3 overall={overall} "
          f"({metrics['wall_s']}s wall)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
