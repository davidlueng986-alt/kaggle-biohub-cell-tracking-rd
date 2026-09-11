#!/usr/bin/env python3
"""EXP-0059 step 3: link (gate 7, global ids) + score frozen-rule assignments.

Det sources: frozen manifests (EXP-0008/0009/0021/0039/0040, verified 100f)
or EXP-0059/det fresh. Scorer v1.1.0 score.score_samples; runtime-only scipy
Hungarian swap (scripts/* untouched) after equivalence gate on one sparse
sample scored both ways (identical edge/div counts required).
Writes pred_*.json, scores.json, metrics.json (cv_tag trusted + HP provenance).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/home/box/workspace/kaggle-biohub-rd"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import baseline_link as BL  # noqa: E402
import score as SCORE  # noqa: E402

EXP = os.path.join(ROOT, "experiments")
GT_DIR = os.path.join(EXP, "EXP-0003", "gt")
MANIFEST = {
    ("44b6_0113de3b", 99.0): ("EXP-0008", "full_44b6_0113de3b"),
    ("44b6_0b24845f", 99.0): ("EXP-0021", "full_44b6_0b24845f"),
    ("44b6_0c582fdc", 99.0): ("EXP-0021", "full_44b6_0c582fdc"),
    ("6bba_05b6850b", 99.0): ("EXP-0008", "full_6bba_05b6850b"),
    ("6bba_05db0fb1", 98.5): ("EXP-0021", "full_6bba_05db0fb1"),
    ("6bba_05db0fb1", 96.0): ("EXP-0039", "full_6bba_05db0fb1"),
    ("44b6_0b24845f", 96.0): ("EXP-0040", "full_44b6_0b24845f"),
    ("44b6_0c582fdc", 96.0): ("EXP-0040", "full_44b6_0c582fdc"),
}
FRAMES = list(range(100))
BTE = {"loso_worst": 0.2092, "micro": 0.4826, "nested_worst": 0.4193}


def enable_fast_hungarian():
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    orig = SCORE._hungarian

    def fast(cost):
        # Same contract as score._hungarian: col_for_row list length n.
        n = len(cost)
        if n == 0:
            return []
        r, c = linear_sum_assignment(np.asarray(cost, dtype=float))
        out = [-1] * n
        for i, j in zip([int(x) for x in r], [int(x) for x in c]):
            out[i] = j
        return out

    SCORE._hungarian = fast
    return orig


def load_nodes(sid, pct):
    nodes, gid, src = [], 0, None
    if (sid, pct) in MANIFEST:
        exp, stem = MANIFEST[(sid, pct)]
        src = f"frozen:{exp}/{stem}"
        paths = [os.path.join(EXP, exp, f"{stem}_t{t}.json") for t in FRAMES]
    else:
        src = "fresh:EXP-0059/det"
        paths = [os.path.join(HERE, "det", f"{sid}_p{pct}_t{t}.json") for t in FRAMES]
    missing = [p for p in paths if not os.path.exists(p)]
    assert not missing, f"det frames missing for {(sid, pct)}: {missing[:3]}"
    for t, p in enumerate(paths):
        det = json.load(open(p))
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    return nodes, gid, src


def link_and_score(sid, pct):
    nodes, n_det, src = load_nodes(sid, pct)
    pred = BL.link({"nodes": nodes, "edges": []}, maxd=7.0)
    gt = json.load(open(os.path.join(GT_DIR, f"{sid}_gt.json")))
    agg = SCORE.score_samples([(sid, pred, gt, None)])
    s = agg["per_sample"][0]
    with open(os.path.join(HERE, f"pred_{sid}_p{pct}.json"), "w") as f:
        json.dump(pred, f)
    return {"edge": s["adjusted_edge_jaccard"], "raw": s["edge_jaccard_raw"],
            "div": s["division_jaccard"], "score": s["score"],
            "ec": s["edge_counts"], "dc": s["division_counts"],
            "n_det": n_det, "det_src": src,
            "backend": pred.get("assign")}


def main():
    assign = json.load(open(os.path.join(HERE, "brightness.json")))
    combos = {("44b6_0b24845f", 99.0), ("44b6_0c582fdc", 99.0),
              ("6bba_05b6850b", 96.0), ("6bba_05db0fb1", 99.0),
              ("6bba_062c8d37", 96.0), ("44b6_0113de3b", 99.0)}
    # Equivalence gate on sparse sample, both Hungarian backends.
    r_slow = link_and_score("44b6_0113de3b", 99.0)
    orig = SCORE._hungarian  # noqa: F841 (already slow path so far)
    enable_fast_hungarian()
    r_fast = link_and_score("44b6_0113de3b", 99.0)
    assert (r_slow["ec"], r_slow["dc"]) == (r_fast["ec"], r_fast["dc"]), "solver mismatch"
    print(f"equiv gate PASS (0113de3b@99 ec={r_fast['ec']}); scipy path live", flush=True)
    scores = {"44b6_0113de3b@99.0": r_fast}
    for sid, pct in sorted(combos - {("44b6_0113de3b", 99.0)}):
        scores[f"{sid}@{pct}"] = link_and_score(sid, pct)
        r = scores[f"{sid}@{pct}"]
        print(f"{sid}@{pct}: edge={r['edge']:.4f} div={r['div']:.4f} "
              f"score={r['score']:.4f} n_det={r['n_det']} [{r['det_src']}]", flush=True)
    json.dump(scores, open(os.path.join(HERE, "scores.json"), "w"), indent=2)

    gt_cache = {sid: json.load(open(os.path.join(GT_DIR, f"{sid}_gt.json")))
                for sid, _ in [("44b6_0113de3b", 0), ("44b6_0b24845f", 0),
                               ("44b6_0c582fdc", 0), ("6bba_05b6850b", 0),
                               ("6bba_05db0fb1", 0), ("6bba_062c8d37", 0)]}
    preds = {k: json.load(open(os.path.join(HERE, f"pred_{k.replace('@', '_p')}.json")))
             for k in scores}

    def micro(keys):
        pairs = [(k.split("@")[0], preds[k], gt_cache[k.split("@")[0]], None) for k in keys]
        agg = SCORE.score_samples(pairs)
        per = {p["sample"]: p for p in agg["per_sample"]}
        return agg, per

    # LOSO holdouts under frozen rule (0113de3b@96 unscored: over 300f cap).
    loso_map = {"44b6_0113de3b": None, "44b6_0b24845f": "44b6_0b24845f@99.0",
                "44b6_0c582fdc": "44b6_0c582fdc@99.0",
                "6bba_05b6850b": "6bba_05b6850b@96.0",
                "6bba_05db0fb1": "6bba_05db0fb1@99.0",
                "6bba_062c8d37": "6bba_062c8d37@96.0"}
    scored_keys = [v for v in loso_map.values() if v]
    _, per5 = micro(scored_keys)
    import numpy as np
    w = np.array([per5[k.split("@")[0]]["weight"] if "weight" in per5[k.split("@")[0]]
                  else per5[k.split("@")[0]]["edge_counts"]["TP"]
                  + per5[k.split("@")[0]]["edge_counts"]["FP"]
                  + per5[k.split("@")[0]]["edge_counts"]["FN"] for k in scored_keys],
                 dtype=float)
    adj = np.array([scores[k]["edge"] for k in scored_keys])
    partial_micro = float((w * adj).sum() / w.sum())
    dTP = sum(scores[k]["dc"]["TP"] for k in scored_keys)
    dFP = sum(scores[k]["dc"]["FP"] for k in scored_keys)
    dFN = sum(scores[k]["dc"]["FN"] for k in scored_keys)
    partial_div = dTP / (dTP + dFP + dFN) if (dTP + dFP + dFN) else 1.0
    loso_worst5 = min(scores[k]["score"] for k in scored_keys)

    # Nested arms (both complete 3/3).
    n44 = ["6bba_05b6850b@96.0", "6bba_05db0fb1@99.0", "6bba_062c8d37@96.0"]
    n66 = ["44b6_0113de3b@99.0", "44b6_0b24845f@99.0", "44b6_0c582fdc@99.0"]
    agg44, per44 = micro(n44)
    agg66, per66 = micro(n66)

    def arm_micro2(keys, per):
        ww = sum(per[k.split("@")[0]]["edge_counts"][c]
                 for k in keys for c in ("TP", "FP", "FN"))
        return sum(scores[k]["edge"] * sum(per[k.split("@")[0]]["edge_counts"][c]
                   for c in ("TP", "FP", "FN")) for k in keys) / ww
    m44 = arm_micro2(n44, per44)
    m66 = arm_micro2(n66, per66)

    metrics = {
        "protocol_version": "1.2", "cv_tag": "trusted", "scorer_version": "1.1.0",
        "exp_id": "EXP-0059", "title": "Nested binary-darkness rule",
        "hypothesis_id": "H-002", "dry_run": False, "real_data": True,
        "image_based": True, "simplified_scorer": False,
        "rule": {"proxy": "frame-mean intensity t20-29 (GT-free)",
                 "cut": "fit-median", "below_or_equal": 96.0, "above": 99.0,
                 "gate": 7.0, "frozen": True},
        "brightness": assign["B"],
        "loso_table": {},
        "loso_partial_5of6": {
            "scored": sorted(scored_keys),
            "unscored": ["44b6_0113de3b@96.0 (over 300f cap; scored worst 0.1610 already settles the bar)"],
            "worst": loso_worst5,
            "micro_edge_partial": partial_micro,
            "div_micro_partial": partial_div,
        },
        "embryo_nested": {
            "fit_44b6_apply_6bba": {"HP": ["fit-median", 96.0, 99.0, 7.0],
                                    "micro": m44, "complete_3of3": True},
            "fit_6bba_apply_44b6": {"HP": ["fit-median", 96.0, 99.0, 7.0],
                                    "micro": m66, "complete_3of3": True},
            "nested_worst": min(m44, m66),
        },
        "BTE": BTE,
        "decision": "keep-trying",
    }
    for sid in ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
                "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]:
        fold = assign["loso"][sid]
        key = loso_map[sid]
        row = {"fit_on": fold["fit_on"], "fit_median": fold["fit_median"],
               "B_holdout": fold["B_holdout"], "assigned_pct": fold["assigned_pct"],
               "gate": 7.0}
        if key:
            row.update(scores[key])
        else:
            row["status"] = "unscored_over_cap"
        metrics["loso_table"][sid] = row
    json.dump(metrics, open(os.path.join(HERE, "metrics.json"), "w"), indent=2)
    print(f"LOSO-partial worst={loso_worst5:.4f} micro5={partial_micro:.4f} | "
          f"nested m44={m44:.4f} m66={m66:.4f} worst={min(m44, m66):.4f}", flush=True)


if __name__ == "__main__":
    main()
