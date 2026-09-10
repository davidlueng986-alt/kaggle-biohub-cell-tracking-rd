#!/usr/bin/env python3
"""EXP-0038 metrics assembler (called by run.sh).

Reads filter stats + score.py --out JSONs (no re-scoring: score_single's
Hungarian matching is expensive on the 26k-node sample) and writes the
before/after table + gate verdict to metrics.json.
"""

import json
import sys

EXP = "experiments/EXP-0038"
SAMPLES = ["6bba_05b6850b", "6bba_05db0fb1"]


def load(p):
    with open(p) as f:
        return json.load(f)


def main():
    rows = {}
    for name in SAMPLES:
        unf = load(f"{EXP}/score_unfilt_{name}.json")["per_sample"][0]
        flt = load(f"{EXP}/score_filt_{name}.json")["per_sample"][0]
        gt = load(f"experiments/EXP-0003/gt/{name}_gt.json")
        fstats = load(f"{EXP}/filt_{name}_stats.json")
        n_gt = len(gt["nodes"])
        r = {
            "before": {
                "raw": unf["edge_jaccard_raw"],
                "adj": unf["adjusted_edge_jaccard"],
                "div": unf["division_jaccard"],
                "score": unf["score"],
                "edge_counts": unf["edge_counts"],
                "division_counts": unf["division_counts"],
                "T_pred": unf["T_pred"],
                "T_true": unf["T_true"],
                "T_ratio": unf["T_pred"] / unf["T_true"],
                "det": unf["T_pred"],
                "edges": None,  # filled below from frozen pred
                "recall": unf["n_gt_matched"] / n_gt,
                "n_gt_matched": unf["n_gt_matched"],
                "n_gt_nodes": n_gt,
            },
            "after": {
                "raw": flt["edge_jaccard_raw"],
                "adj": flt["adjusted_edge_jaccard"],
                "div": flt["division_jaccard"],
                "score": flt["score"],
                "edge_counts": flt["edge_counts"],
                "division_counts": flt["division_counts"],
                "T_pred": flt["T_pred"],
                "T_true": flt["T_true"],
                "T_ratio": flt["T_pred"] / flt["T_true"],
                "det": flt["T_pred"],
                "edges": None,
                "recall": flt["n_gt_matched"] / n_gt,
                "n_gt_matched": flt["n_gt_matched"],
                "n_gt_nodes": n_gt,
            },
            "filter_stats": fstats,
        }
        b, a = r["before"], r["after"]
        tp0 = b["edge_counts"]["TP"]
        r["delta"] = {
            "d_adj": a["adj"] - b["adj"],
            "d_raw": a["raw"] - b["raw"],
            "d_recall": a["recall"] - b["recall"],
            "edge_TP_loss_frac": (tp0 - a["edge_counts"]["TP"]) / tp0 if tp0 else 0.0,
            "d_FP": a["edge_counts"]["FP"] - b["edge_counts"]["FP"],
        }
        rows[name] = r

    # edge counts before/after from the pred graphs (cheap: len only)
    frozen = {
        "6bba_05b6850b": "experiments/EXP-0009/full_6bba_05b6850b_pred.json",
        "6bba_05db0fb1": "experiments/EXP-0021/6bba_05db0fb1_pred.json",
    }
    for name in SAMPLES:
        rows[name]["before"]["edges"] = len(load(frozen[name])["edges"])
        rows[name]["after"]["edges"] = len(
            load(f"{EXP}/filt_{name}_pred.json")["edges"])

    gate = {}
    for name in SAMPLES:
        d = rows[name]["delta"]
        gate[name] = {
            "adj_gain_ge_0.02": d["d_adj"] >= 0.02,
            "recall_loss_le_0.005": (rows[name]["before"]["recall"]
                                     - rows[name]["after"]["recall"]) <= 0.005,
            "FP_down": d["d_FP"] < 0,
        }
    worst_adj = min(rows[n]["delta"]["d_adj"] for n in SAMPLES)
    overall = all(
        gate[n]["adj_gain_ge_0.02"] and gate[n]["recall_loss_le_0.005"]
        and gate[n]["FP_down"] for n in SAMPLES)
    metrics = {
        "exp_id": "EXP-0038",
        "title": "T-discipline track filter",
        "status": "done",
        "scorer": "scripts/score.py v1.1.0 (PROTOCOL v1.1, true T_true from GT)",
        "filter": ("min-track-len 6 frames + prune-isolated + "
                   "frac-capped rescue (5% of kept, longest-first, whole tracks)"),
        "per_sample": rows,
        "gate": {
            "per_sample": gate,
            "worst_of_2_adj_gain": worst_adj,
            "bar": ("worst-of-2 adj gain >= +0.02 AND recall loss <= 0.005 "
                    "AND FP down"),
            "pass": overall,
            "verdict": "GO" if overall else "STOP (park filtering)",
        },
    }
    with open(f"{EXP}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics["gate"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
