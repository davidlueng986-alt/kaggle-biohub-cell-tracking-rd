#!/usr/bin/env python3
"""AUDIT-FIX A2 differential harness: repo scripts/score.py division vs official oracle.

Oracle pin: tracking_cellmot 0.1.0 @ 075fc5f5a52d11077f9dc2b074644618f26939e2
  (/tmp/opencode/official clone of royerlab/kaggle-cell-tracking-competition,
  main 2026-07-17), with tracksdata 0.1.0rc10 / scipy 1.18.1 / polars 1.44.2.

Scope: S4 (component check: direct-child precedence, no unordered-set scan,
rename-stable), S5 (fork poison over ALL branches), S6 (GT ==2, pred >=2),
S7 (considered-FP class), S11 (per-window rematch), S12 (+-1tp pinned to 1).
Match/filter/dedup (S1-S3, A1) and aggregate (S8-S10/S13, A3) are NOT compared
here.

Run: /tmp/opencode/venv-oracle/bin/python RESULTS/EXP-AUDIT-00/diff_a2.py [--fuzz N] [--seed S]
Exit 0 iff every a2_* fixture has division-count diff = 0.
Writes diff_report_a2.json next to this script (diff_report.json stays A1-owned).
"""
import json
import os
import random
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import score as S  # noqa: E402

warnings.filterwarnings("ignore")
from tracksdata.options import set_options

set_options(show_progress=False)


def load_fixture(path):
    with open(path) as f:
        return json.load(f)


def gdict(nodes, edges):
    return {
        "nodes": [{"id": i, "t": t, "z": z, "y": y, "x": x}
                  for (i, t, z, y, x) in nodes],
        "edges": [list(e) for e in edges],
    }


def repo_eval(fx):
    pred = gdict(fx["pred"]["nodes"], fx["pred"]["edges"])
    gt = gdict(fx["gt"]["nodes"], fx["gt"]["edges"])
    vx = tuple(fx["voxel"])
    md = fx["max_dist"]
    p2g, g2p = S.match_nodes(pred["nodes"], gt["nodes"], voxel=vx, max_dist=md)
    dc = S.division_counts(pred["nodes"], [tuple(e) for e in pred["edges"]],
                           gt["nodes"], [tuple(e) for e in gt["edges"]],
                           p2g, g2p, voxel=vx, max_dist=md)
    return dc


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
    for (i, t, z, y, x) in sorted(nodes, key=lambda r: r[0]):
        nid = g.add_node({"t": int(t), "z": float(z), "y": float(y),
                          "x": float(x)})
        f2g[i] = nid
    for (u, v) in edges:
        g.add_edge(f2g[u], f2g[v], {})
    return g


def oracle_eval(fx):
    from tracking_cellmot.division_metrics import evaluate_divisions
    vx = tuple(fx["voxel"])
    md = fx["max_dist"]
    pred_g = _build_graph(fx["pred"]["nodes"], fx["pred"]["edges"])
    gt_g = _build_graph(fx["gt"]["nodes"], fx["gt"]["edges"])
    r = evaluate_divisions(pred_g, gt_g, scale=vx, max_distance=md)
    return {"TP": r.tp, "FP": r.fp, "FN": r.fn}


def run_fixtures():
    fxdir = os.path.join(HERE, "fixtures")
    report = {"oracle_pin": {
        "repo": "https://github.com/royerlab/kaggle-cell-tracking-competition",
        "commit": "075fc5f5a52d11077f9dc2b074644618f26939e2",
        "package": "tracking-cellmot 0.1.0",
        "tracksdata": "0.1.0rc10", "scipy": "1.18.1", "polars": "1.44.2",
        "path": "/tmp/opencode/official",
    }, "fixtures": []}
    ok = True
    for fn in sorted(os.listdir(fxdir)):
        if not fn.startswith("a2_") or not fn.endswith(".json"):
            continue
        fx = load_fixture(os.path.join(fxdir, fn))
        rc = repo_eval(fx)
        oc = oracle_eval(fx)
        diff = 0 if rc == oc else 1
        pinned = fx.get("oracle", {}).get("division_counts")
        pin_ok = (pinned == oc)
        row = {"fixture": fx["name"], "audit_ids": fx.get("audit_ids", []),
               "repo_counts": rc, "oracle_counts": oc, "count_diff": diff,
               "pinned_oracle_match": bool(pin_ok)}
        report["fixtures"].append(row)
        status = "OK " if diff == 0 else "DIFF"
        if diff:
            ok = False
        print(f"[{status}] {fx['name']}: count_diff={diff} pinned={row['pinned_oracle_match']}")
        if diff:
            print(f"   repo   {rc}")
            print(f"   oracle {oc}")
    return report, ok


def _rand_div_graph(rng, id0, t0, y0, jitter=0.0, drop_branch=False,
                    extra_fork=False, three_child=False):
    """Build one GT division window + matching pred window (fixture ids)."""
    gtn = [(id0, t0, 0, y0, 0), (id0 + 1, t0 + 1, 0, y0, 0),
           (id0 + 2, t0 + 2, 0, y0, 0), (id0 + 3, t0 + 2, 0, y0 + 10, 0),
           (id0 + 4, t0 + 3, 0, y0, 0), (id0 + 5, t0 + 3, 0, y0 + 10, 0)]
    gte = [(id0, id0 + 1), (id0 + 1, id0 + 2), (id0 + 1, id0 + 3),
           (id0 + 2, id0 + 4), (id0 + 3, id0 + 5)]
    if three_child:
        gtn.append((id0 + 6, t0 + 2, 0, y0 + 20, 0))
        gtn.append((id0 + 7, t0 + 3, 0, y0 + 20, 0))
        gte += [(id0 + 1, id0 + 6), (id0 + 6, id0 + 7)]
    j = lambda: rng.uniform(-jitter, jitter)
    pn = [(2000 + id0, t0, 0, y0 + j(), 0), (2000 + id0 + 1, t0 + 1, 0, y0 + j(), 0),
          (2000 + id0 + 2, t0 + 2, 0, y0 + j(), 0), (2000 + id0 + 3, t0 + 2, 0, y0 + 10 + j(), 0),
          (2000 + id0 + 4, t0 + 3, 0, y0 + j(), 0), (2000 + id0 + 5, t0 + 3, 0, y0 + 10 + j(), 0)]
    pe = [(2000 + id0, 2000 + id0 + 1), (2000 + id0 + 1, 2000 + id0 + 2),
          (2000 + id0 + 1, 2000 + id0 + 3), (2000 + id0 + 2, 2000 + id0 + 4),
          (2000 + id0 + 3, 2000 + id0 + 5)]
    if three_child:
        pn.append((2000 + id0 + 6, t0 + 2, 0, y0 + 20 + j(), 0))
        pn.append((2000 + id0 + 7, t0 + 3, 0, y0 + 20 + j(), 0))
        pe += [(2000 + id0 + 1, 2000 + id0 + 6), (2000 + id0 + 6, 2000 + id0 + 7)]
    if drop_branch:
        pn = [r for r in pn if r[0] not in (2000 + id0 + 3, 2000 + id0 + 5)]
        pe = [e for e in pe if e[0] not in (2000 + id0 + 3,) and e[1] not in (2000 + id0 + 3, 2000 + id0 + 5)]
    if extra_fork:
        pn += [(9000 + id0, t0 + 1, 0, y0 + 50, 0), (9000 + id0 + 1, t0 + 2, 0, y0 + 50, 0),
               (9000 + id0 + 2, t0 + 2, 0, y0 + 60, 0)]
        pe += [(9000 + id0, 9000 + id0 + 1), (9000 + id0, 9000 + id0 + 2)]
    return (pn, pe), (gtn, gte)


def fuzz(n, seed):
    rng = random.Random(seed)
    n_diff = 0
    for it in range(n):
        jitter = rng.choice([0.0, 0.5, 1.5])
        drop = rng.random() < 0.25
        extra = rng.random() < 0.25
        three = rng.random() < 0.15
        (pn, pe), (gn, ge) = _rand_div_graph(rng, 10, 0, 0.0, jitter, drop, extra, three)
        # occasional second distant division (multi-window + cross-component)
        if rng.random() < 0.4:
            (pn2, pe2), (gn2, ge2) = _rand_div_graph(rng, 500, 0, 100.0, jitter, False, False, False)
            pn, pe, gn, ge = pn + pn2, pe + pe2, gn + gn2, ge + ge2
        fx = {"name": f"fuzz{it}", "voxel": [1.0, 1.0, 1.0], "max_dist": 7.0,
              "pred": {"nodes": pn, "edges": pe}, "gt": {"nodes": gn, "edges": ge}}
        rc = repo_eval(fx)
        oc = oracle_eval(fx)
        if rc != oc:
            n_diff += 1
            print(f"[FUZZ-DIFF {it}] repo={rc} oracle={oc} jitter={jitter} drop={drop} extra={extra} three={three}")
            print(f"             fixture={json.dumps(fx)}")
            if n_diff >= 5:
                print("... stopping after 5 fuzz diffs")
                break
    print(f"fuzz: {n} scenes, {n_diff} diffs (seed={seed})")
    return n_diff


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuzz", type=int, default=0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    report, ok = run_fixtures()
    fuzz_diff = 0
    if args.fuzz:
        fuzz_diff = fuzz(args.fuzz, args.seed)
        report["fuzz"] = {"n": args.fuzz, "seed": args.seed, "diffs": fuzz_diff}
    with open(os.path.join(HERE, "diff_report_a2.json"), "w") as f:
        json.dump(report, f, indent=2)
    print("wrote diff_report_a2.json")
    sys.exit(0 if (ok and fuzz_diff == 0) else 1)


if __name__ == "__main__":
    main()
