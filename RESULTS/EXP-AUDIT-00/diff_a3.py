#!/usr/bin/env python3
"""AUDIT-FIX A3 differential harness: repo scripts/score.py aggregate vs official.

Oracle pin: tracking_cellmot 0.1.0 @ 075fc5f5a52d11077f9dc2b074644618f26939e2
  (/tmp/opencode/official clone of royerlab/kaggle-cell-tracking-competition,
  main 2026-07-17), with tracksdata 0.1.0rc10 / scipy 1.18.1 / polars 1.44.2.

Scope: S8 (T_true GT-only), S9 (zero-division term dropped), S10
(zero-count exclusion, edge 0/0 NaN, w_i weighting), S13 (duplicate node
ids). Core match/filter/dedup (S1-S3, A1) and division rules (S4-S7, A2)
are exercised only as pass-through; all fixtures are division-free so the
division comparison is trivially 0 == 0.

Oracle path mirrors official scripts/evaluate.py exactly: evaluate() per
pair -> per_sample_metrics(er, n_total=GT T_true or NaN, recall) ->
summarise(rows). n_total NEVER falls back to pred (S8).

Run: /tmp/opencode/venv-oracle/bin/python RESULTS/EXP-AUDIT-00/diff_a3.py
Exit 0 iff every fixture has aggregate diff = 0 AND live oracle reproduces
the frozen pin. Writes a3_report.json next to this script.
"""
import json
import math
import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import score as S  # noqa: E402

warnings.filterwarnings("ignore")
from tracksdata.options import set_options

set_options(show_progress=False)

TOL = 1e-9


def is_nan(x):
    return isinstance(x, float) and math.isnan(x)


def feq(a, b):
    """NaN-aware float equality (NaN == NaN, else abs tol)."""
    if a is None or b is None:
        return a is None and b is None
    a = float(a)
    b = float(b)
    if math.isnan(a) and math.isnan(b):
        return True
    if math.isnan(a) or math.isnan(b):
        return False
    return abs(a - b) <= TOL


def jsafe(x):
    return "NaN" if is_nan(x) else x


def gdict(sample_side):
    return {
        "nodes": [{"id": i, "t": t, "z": z, "y": y, "x": x}
                  for (i, t, z, y, x) in sample_side["nodes"]],
        "edges": [list(e) for e in sample_side["edges"]],
    }


def repo_eval(fx):
    pairs = []
    for smp in fx["samples"]:
        pred = gdict(smp["pred"])
        if "T_true" in smp["pred"]:
            pred["T_true"] = smp["pred"]["T_true"]
        gt = gdict(smp["gt"])
        if "T_true" in smp["gt"]:
            gt["T_true"] = smp["gt"]["T_true"]
        pairs.append((smp["name"], pred, gt, None))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        agg = S.score_samples(pairs, voxel=tuple(fx["voxel"]),
                              max_dist=fx["max_dist"])
    per = [{"sample": s["sample"],
            "edge_counts": dict(s["edge_counts"]),
            "division_counts": dict(s["division_counts"]),
            "adj": s["adjusted_edge_jaccard"],
            "div": s["division_jaccard"]}
           for s in agg["per_sample"]]
    return {"per": per,
            "adj": agg["adjusted_edge_jaccard"],
            "div": agg["division_jaccard"],
            "score": agg["score"],
            "n_adj": agg["n_adj"]}


def _build_graph(nodes, edges):
    import polars as pl
    import tracksdata as td
    g = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        try:
            g.add_node_attr_key(key, pl.Float64, 0.0)
        except Exception:
            pass
    f2g = {}
    for (i, t, z, y, x) in nodes:
        # NOTE: fixture rows may share node ids (S13); tracksdata assigns a
        # fresh internal id per ROW, exactly like official csv_to_geffs.
        nid = g.add_node({"t": int(t), "z": float(z), "y": float(y),
                          "x": float(x)})
        f2g.setdefault(i, []).append(nid)
    # official id_map last-wins for duplicated node ids (S13 pin)
    id_map = {i: v[-1] for i, v in f2g.items()}
    for (u, v) in edges:
        g.add_edge(id_map[u], id_map[v], {})
    return g


def oracle_eval(fx):
    from tracking_cellmot.metrics import (evaluate, node_recall,
                                          per_sample_metrics, summarise)
    rows = []
    per = []
    skipped = []
    for smp in fx["samples"]:
        pred_g = _build_graph(smp["pred"]["nodes"], smp["pred"]["edges"])
        gt_g = _build_graph(smp["gt"]["nodes"], smp["gt"]["edges"])
        # official scripts/evaluate.py:evaluate_pairs wraps each sample in
        # try/except and SKIPS unreadable/crashing samples. The pinned
        # oracle crashes on empty pred+empty gt (TypeError in division
        # matching) and on nonempty pred+empty gt (SchemaError in the
        # division join); the repo instead NaN-skips those samples at
        # aggregation. Both mechanisms exclude the sample: mirror the skip.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                er = evaluate(pred_g, gt_g, scale=tuple(fx["voxel"]),
                              max_distance=fx["max_dist"])
        except Exception as e:
            skipped.append({"sample": smp["name"],
                            "error": f"{type(e).__name__}: {e}"})
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if pred_g.num_edges() > 0 and pred_g.num_nodes() > 0:
                recall = node_recall(pred_g, gt_g)
            else:
                recall = 0.0
        n_total = float(smp["gt"]["T_true"]) if "T_true" in smp["gt"] \
            else float("nan")
        row = per_sample_metrics(er, n_total, recall)
        rows.append(row)
        per.append({"sample": smp["name"],
                    "edge_counts": {"TP": er.edge_tp, "FP": er.edge_fp,
                                    "FN": er.edge_fn},
                    "division_counts": {"TP": er.division_tp,
                                        "FP": er.division_fp,
                                        "FN": er.division_fn},
                    "adj": row["adj_edge_jaccard"]})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        s = summarise(rows)
    return {"per": per, "adj": s["adj_edge_jaccard"],
            "div": s["division_jaccard"], "score": s["score"],
            "n_adj": s["n_adj"], "skipped": skipped}


def compare_fixture(fx):
    r = repo_eval(fx)
    o = oracle_eval(fx)
    diffs = []
    ro = {p["sample"]: p for p in r["per"]}
    oo = {p["sample"]: p for p in o["per"]}
    for name, op in oo.items():
        rp = ro[name]
        for k in ("TP", "FP", "FN"):
            if rp["edge_counts"][k] != op["edge_counts"][k]:
                diffs.append(f"{name}.edge_{k}: "
                             f"repo={rp['edge_counts'][k]} "
                             f"oracle={op['edge_counts'][k]}")
        for k in ("TP", "FP", "FN"):
            if rp["division_counts"][k] != op["division_counts"][k]:
                diffs.append(f"{name}.div_{k}: "
                             f"repo={rp['division_counts'][k]} "
                             f"oracle={op['division_counts'][k]}")
        if not feq(rp["adj"], op["adj"]):
            diffs.append(f"{name}.adj: repo={rp['adj']} "
                         f"oracle={op['adj']}")
    # oracle-skipped (crashed) samples must be NaN-excluded repo-side:
    # same aggregate effect via different mechanisms (documented above).
    for sk in o["skipped"]:
        rp = ro[sk["sample"]]
        w = sum(rp["edge_counts"].values())
        if not (is_nan(rp["adj"]) and w == 0):
            diffs.append(f"{sk['sample']}.skip-parity: oracle skipped "
                         f"({sk['error']}) but repo adj={rp['adj']} w={w}")
    for k in ("adj", "div", "score"):
        if not feq(r[k], o[k]):
            diffs.append(f"aggregate.{k}: repo={r[k]} oracle={o[k]}")
    if r["n_adj"] != o["n_adj"]:
        diffs.append(f"aggregate.n_adj: repo={r['n_adj']} "
                     f"oracle={o['n_adj']}")
    # frozen-pin check (live oracle must reproduce the pinned values)
    pinned = fx.get("oracle")
    pin_ok = None
    if pinned:
        pin_ok = (feq(pinned.get("adj"), o["adj"])
                  and feq(pinned.get("div"), o["div"])
                  and feq(pinned.get("score"), o["score"])
                  and pinned.get("n_adj") == o["n_adj"]
                  and pinned.get("skipped") == sorted(
                      sk["sample"] for sk in o["skipped"])
                  and all(
                      next(q for q in pinned.get("per", [])
                           if q["sample"] == p["sample"])["edge_counts"]
                      == p["edge_counts"]
                      for p in o["per"]))
    return r, o, diffs, pin_ok


def run_fixtures():
    fxdir = os.path.join(HERE, "fixtures")
    report = {"oracle_pin": {
        "repo": "https://github.com/royerlab/kaggle-cell-tracking-competition",
        "commit": "075fc5f5a52d11077f9dc2b074644618f26939e2",
        "package": "tracking-cellmot 0.1.0",
        "tracksdata": "0.1.0rc10", "scipy": "1.18.1", "polars": "1.44.2",
        "path": "/tmp/opencode/official",
    }, "scorer_version": S.SCORER_VERSION, "fixtures": []}
    ok = True
    for fn in sorted(os.listdir(fxdir)):
        if not fn.startswith("a3_") or not fn.endswith(".json"):
            continue
        with open(os.path.join(fxdir, fn)) as f:
            fx = json.load(f)
        r, o, diffs, pin_ok = compare_fixture(fx)
        good = not diffs and pin_ok is not False
        ok = ok and good
        status = "OK " if good else "DIFF"
        print(f"[{status}] {fx['name']}: {len(diffs)} diffs "
              f"pinned={pin_ok} repo(adj={jsafe(r['adj'])} "
              f"div={jsafe(r['div'])} score={jsafe(r['score'])} "
              f"n_adj={r['n_adj']}) "
              f"oracle(adj={jsafe(o['adj'])} div={jsafe(o['div'])} "
              f"score={jsafe(o['score'])} n_adj={o['n_adj']})")
        for d in diffs:
            print(f"    - {d}")
        report["fixtures"].append({
            "fixture": fx["name"], "audit_ids": fx.get("audit_ids", []),
            "repo": {"per": [{**p, "adj": jsafe(p["adj"]),
                              "div": jsafe(p["div"])} for p in r["per"]],
                     "adj": jsafe(r["adj"]), "div": jsafe(r["div"]),
                     "score": jsafe(r["score"]), "n_adj": r["n_adj"]},
            "oracle_live": {"per": [{**p, "adj": jsafe(p["adj"])}
                                    for p in o["per"]],
                            "adj": jsafe(o["adj"]), "div": jsafe(o["div"]),
                            "score": jsafe(o["score"]),
                            "n_adj": o["n_adj"],
                            "skipped": o["skipped"]},
            "diffs": diffs, "pinned_oracle_match": pin_ok})
    return report, ok


def main():
    report, ok = run_fixtures()
    with open(os.path.join(HERE, "a3_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print("wrote a3_report.json")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
