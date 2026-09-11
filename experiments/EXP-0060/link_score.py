#!/usr/bin/env python3
"""EXP-0060 step 3: link (gate 7, global ids) + score sign-corrected assignments.

Det sources: frozen manifests (EXP-0008/0039/0040, verified 100f) or
EXP-0060/det fresh. Scorer v1.1.0 score.score_samples; runtime-only scipy
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
    ("6bba_05b6850b", 99.0): ("EXP-0008", "full_6bba_05b6850b"),
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
        src = "fresh:EXP-0060/det"
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
    combos = {("44b6_0113de3b", 99.0), ("44b6_0b24845f", 96.0),
              ("44b6_0c582fdc", 96.0), ("6bba_05b6850b", 99.0),
              ("6bba_05db0fb1", 96.0), ("6bba_062c8d37", 99.0),
              ("44b6_0113de3b", 96.0)}
    # Equivalence gate on sparse sample, both Hungarian backends.
    r_slow = link_and_score("44b6_0113de3b", 99.0)
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
                for sid in ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
                            "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]}
    preds = {k: json.load(open(os.path.join(HERE, f"pred_{k.replace('@', '_p')}.json")))
             for k in scores}

    def agg_of(keys):
        pairs = [(k.split("@")[0], preds[k], gt_cache[k.split("@")[0]], None) for k in keys]
        return SCORE.score_samples(pairs)

    # LOSO holdouts under sign-corrected rule (complete 6/6).
    loso_map = {"44b6_0113de3b": "44b6_0113de3b@99.0",
                "44b6_0b24845f": "44b6_0b24845f@96.0",
                "44b6_0c582fdc": "44b6_0c582fdc@96.0",
                "6bba_05b6850b": "6bba_05b6850b@99.0",
                "6bba_05db0fb1": "6bba_05db0fb1@96.0",
                "6bba_062c8d37": "6bba_062c8d37@99.0"}
    for sid, key in loso_map.items():
        assert assign["loso"][sid]["assigned_pct"] == float(key.split("@")[1]), \
            f"assignment drift {sid}: brightness.json vs loso_map"
    loso_keys = sorted(loso_map.values())
    loso_agg = agg_of(loso_keys)
    loso_worst = min(scores[k]["score"] for k in loso_keys)

    # Nested arms, both complete 3/3 (sign-corrected assignments verified).
    n_fit44 = ["6bba_05b6850b@99.0", "6bba_05db0fb1@96.0", "6bba_062c8d37@99.0"]
    n_fit66 = ["44b6_0113de3b@96.0", "44b6_0b24845f@96.0", "44b6_0c582fdc@96.0"]
    for sid in ["6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]:
        exp_key = {"6bba_05b6850b": n_fit44[0], "6bba_05db0fb1": n_fit44[1],
                   "6bba_062c8d37": n_fit44[2]}[sid]
        assert assign["nested"][sid]["assigned_pct"] == float(exp_key.split("@")[1]), \
            f"nested drift {sid}"
    for sid in ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc"]:
        assert assign["nested"][sid]["assigned_pct"] == 96.0, f"nested drift {sid}"
    agg44 = agg_of(n_fit44)
    agg66 = agg_of(n_fit66)
    nested_worst = min(agg44["adjusted_edge_jaccard"], agg66["adjusted_edge_jaccard"])

    micro = loso_agg["adjusted_edge_jaccard"]
    div_micro = loso_agg["division_jaccard"]
    bars = {"loso_worst": loso_worst > BTE["loso_worst"],
            "micro": micro > BTE["micro"],
            "nested_worst": nested_worst > BTE["nested_worst"]}
    decision = "CANDIDATE" if all(bars.values()) else "keep-trying"

    metrics = {
        "protocol_version": "1.2", "cv_tag": "trusted", "scorer_version": "1.1.0",
        "exp_id": "EXP-0060", "title": "Sign-corrected nested binary-brightness rule",
        "hypothesis_id": "H-002", "dry_run": False, "real_data": True,
        "image_based": True, "simplified_scorer": False,
        "rule": {"proxy": "frame-mean intensity t20-29 (GT-free)",
                 "cut": "fit-median", "above": 96.0, "below_or_equal": 99.0,
                 "gate": 7.0, "frozen": True,
                 "note": "sign-corrected vs EXP-0059: HIGH-B -> 96.0 / LOW-B -> 99.0"},
        "brightness": assign["B"],
        "loso_table": {},
        "loso": {
            "keys": loso_keys,
            "worst": loso_worst,
            "micro_edge": micro,
            "div_micro": div_micro,
            "score_micro": loso_agg["score"],
            "complete_6of6": True,
        },
        "embryo_nested": {
            "fit_44b6_apply_6bba": {"HP": ["fit-median", 96.0, 99.0, 7.0],
                                    "keys": n_fit44,
                                    "micro": agg44["adjusted_edge_jaccard"],
                                    "complete_3of3": True},
            "fit_6bba_apply_44b6": {"HP": ["fit-median", 96.0, 99.0, 7.0],
                                    "keys": n_fit66,
                                    "micro": agg66["adjusted_edge_jaccard"],
                                    "complete_3of3": True},
            "nested_worst": nested_worst,
        },
        "BTE": BTE,
        "bars": bars,
        "decision": decision,
    }
    for sid in ["44b6_0113de3b", "44b6_0b24845f", "44b6_0c582fdc",
                "6bba_05b6850b", "6bba_05db0fb1", "6bba_062c8d37"]:
        fold = assign["loso"][sid]
        key = loso_map[sid]
        row = {"fit_on": fold["fit_on"], "fit_median": fold["fit_median"],
               "B_holdout": fold["B_holdout"], "assigned_pct": fold["assigned_pct"],
               "gate": 7.0}
        row.update(scores[key])
        metrics["loso_table"][sid] = row
    json.dump(metrics, open(os.path.join(HERE, "metrics.json"), "w"), indent=2)
    print(f"LOSO worst={loso_worst:.4f} micro={micro:.4f} div_micro={div_micro:.4f} | "
          f"nested m44={agg44['adjusted_edge_jaccard']:.4f} "
          f"m66={agg66['adjusted_edge_jaccard']:.4f} worst={nested_worst:.4f} | "
          f"bars={bars} -> {decision}", flush=True)


if __name__ == "__main__":
    main()
