#!/usr/bin/env python3
"""AUDIT-FIX A1 differential harness: repo scripts/score.py vs official oracle.

Oracle pin: tracking_cellmot 0.1.0 @ 075fc5f5a52d11077f9dc2b074644618f26939e2
  (/tmp/opencode/official clone of royerlab/kaggle-cell-tracking-competition,
  main 2026-07-17), with tracksdata 0.1.0rc10 / scipy 1.18.1 / polars 1.44.2.

Scope: S1 (node pairing), S2 (consecutive-frame filter), S3 (pred-edge
dedup + merge-collapse + out-degree cap) — i.e. match/filter/dedup only.
Division/aggregate paths are NOT compared here (owned by A2/A3).

Run: /tmp/opencode/venv-oracle/bin/python RESULTS/EXP-AUDIT-00/diff_a1.py [--fuzz N] [--seed S]
Exit 0 iff every fixture has pairing diff = 0 AND edge-count diff = 0.
Writes diff_report.json next to this script.
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
    pred = gdict(*[fx["pred"][k] for k in ("nodes", "edges")])
    gt = gdict(*[fx["gt"][k] for k in ("nodes", "edges")])
    vx = tuple(fx["voxel"])
    md = fx["max_dist"]
    p2g, _ = S.match_nodes(pred["nodes"], gt["nodes"], voxel=vx, max_dist=md)
    ec = S.edge_counts([tuple(e) for e in pred["edges"]],
                       [tuple(e) for e in gt["edges"]], p2g,
                       pred_nodes=pred["nodes"])
    return ({str(k): v for k, v in p2g.items()}, ec)


def _build_graph(nodes, edges):
    import polars as pl
    import tracksdata as td
    g = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        try:
            g.add_node_attr_key(key, pl.Float64, 0.0)
        except Exception:
            pass
    f2g, g2f = {}, {}
    for (i, t, z, y, x) in sorted(nodes, key=lambda r: r[0]):
        nid = g.add_node({"t": int(t), "z": float(z), "y": float(y),
                          "x": float(x)})
        f2g[i] = nid
        g2f[nid] = i
    for (u, v) in edges:
        g.add_edge(f2g[u], f2g[v], {})
    return g, f2g, g2f


def oracle_eval(fx):
    import tracksdata as td
    from tracksdata.metrics import DistanceMatching
    from tracking_cellmot.metrics import evaluate
    vx = tuple(fx["voxel"])
    md = fx["max_dist"]
    pred_g, f2g_p, g2f_p_l = _build_graph(fx["pred"]["nodes"],
                                          fx["pred"]["edges"])
    gt_g, f2g_g, g2f_g = _build_graph(fx["gt"]["nodes"], fx["gt"]["edges"])
    # sanity: edge ids follow insertion order (repo uses list index as edge id)
    if pred_g.num_edges() > 0:
        res = evaluate(pred_g, gt_g, scale=vx, max_distance=md)
        counts = {"TP": res.edge_tp, "FP": res.edge_fp, "FN": res.edge_fn}
    else:
        pred_g.match(gt_g, matching=DistanceMatching(max_distance=md,
                                                     scale=vx))
        counts = {"TP": 0, "FP": 0, "FN": gt_g.num_edges()}
    df = pred_g.node_attrs(attr_keys=[td.DEFAULT_ATTR_KEYS.NODE_ID,
                                      td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID])
    pairing = {}
    for row in df.rows(named=True):
        mid = row[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID]
        if mid is not None and mid != -1:
            pairing[str(g2f_p_l[row[td.DEFAULT_ATTR_KEYS.NODE_ID]])] = g2f_g[mid]
    return pairing, counts


def check_edge_id_order(fx):
    """Assert tracksdata EDGE_IDs follow pred-edge insertion order."""
    import tracksdata as td
    pred_g, f2g, _ = _build_graph(fx["pred"]["nodes"], fx["pred"]["edges"])
    if pred_g.num_edges() == 0:
        return True
    df = pred_g.edge_attrs(attr_keys=[]).sort(td.DEFAULT_ATTR_KEYS.EDGE_ID)
    got = list(zip(df[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE].to_list(),
                   df[td.DEFAULT_ATTR_KEYS.EDGE_TARGET].to_list()))
    inv = {v: k for k, v in f2g.items()}
    got_fx = [(inv[a], inv[b]) for (a, b) in got]
    want = [tuple(e) for e in fx["pred"]["edges"]]
    # tracksdata keeps multiedges, so the full insertion sequence must match
    return got_fx == want


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
        if not fn.endswith(".json"):
            continue
        fx = load_fixture(os.path.join(fxdir, fn))
        rp, rc = repo_eval(fx)
        op, oc = oracle_eval(fx)
        id_ok = check_edge_id_order(fx)
        pair_diff = 0 if rp == op else 1
        cnt_diff = 0 if rc == oc else 1
        pinned = fx.get("oracle", {})
        pin_pair = ({str(k): v for k, v in pinned.get("pairing", {}).items()}
                    == op)
        pin_cnt = (pinned.get("edge_counts") == oc)
        row = {"fixture": fx["name"], "audit_ids": fx.get("audit_ids", []),
               "repo_pairing": rp, "oracle_pairing": op,
               "pair_diff": pair_diff,
               "repo_counts": rc, "oracle_counts": oc, "count_diff": cnt_diff,
               "pinned_oracle_match": bool(pin_pair and pin_cnt),
               "edge_id_order_ok": bool(id_ok)}
        report["fixtures"].append(row)
        status = "OK " if (pair_diff == 0 and cnt_diff == 0) else "DIFF"
        if pair_diff or cnt_diff:
            ok = False
        print(f"[{status}] {fx['name']}: pair_diff={pair_diff} "
              f"count_diff={cnt_diff} pinned={row['pinned_oracle_match']} "
              f"edgeid={row['edge_id_order_ok']}")
        if pair_diff or cnt_diff:
            print(f"   repo   pair={rp} counts={rc}")
            print(f"   oracle pair={op} counts={oc}")
    return report, ok


def fuzz(n, seed):
    rng = random.Random(seed)
    n_diff = 0
    for it in range(n):
        hard = (it % 2 == 1)
        T = rng.randint(2, 4)
        pid, gid = 0, 0
        pn, gn = [], []
        spread = 12 if hard else 30
        for t in range(T):
            for _ in range(rng.randint(1, 4)):
                pid += 1
                pn.append([pid, t, 0, rng.randint(0, spread),
                           rng.randint(0, spread)])
            for _ in range(rng.randint(1, 4)):
                gid += 1
                gn.append([1000 + gid, t, 0, rng.randint(0, spread),
                           rng.randint(0, spread)])
        tids = {}
        for (i, t, z, y, x) in pn:
            tids[i] = t
        pe = []
        for _ in range(rng.randint(0, 12 if hard else 8)):
            u = rng.choice(pn)[0]
            vs = [r[0] for r in pn
                  if tids[r[0]] >= tids[u] and r[0] != u]
            if vs:
                pe.append([u, rng.choice(vs)])
        if pe and rng.random() < 0.4:
            pe.append(list(rng.choice(pe)))  # duplicate edge
        if hard and len(pn) >= 4:  # high out-degree from one source
            u = rng.choice(pn)[0]
            for v in rng.sample([r[0] for r in pn if r[0] != u],
                                min(4, len(pn) - 1)):
                pe.append([u, v])
        ge = []
        gids = [r[0] for r in gn]
        for _ in range(rng.randint(0, 8 if hard else 6)):
            u = rng.choice(gids)
            v = rng.choice(gids)
            if u != v:
                ge.append([u, v])
        if ge and rng.random() < 0.3:
            ge.append(list(rng.choice(ge)))  # duplicate GT edge
        md = rng.choice([3.0, 5.0, 8.0]) if hard else 8.0
        fx = {"name": f"fuzz{it}", "voxel": [1.0, 1.0, 1.0],
              "max_dist": md,
              "pred": {"nodes": pn, "edges": pe},
              "gt": {"nodes": gn, "edges": ge}}
        rp, rc = repo_eval(fx)
        op, oc = oracle_eval(fx)
        if rp != op or rc != oc:
            n_diff += 1
            print(f"[FUZZ-DIFF {it}] repo pair={rp} counts={rc}")
            print(f"             oracle pair={op} counts={oc}")
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
        report["fuzz"] = {"n": args.fuzz, "seed": args.seed,
                          "diffs": fuzz_diff}
    with open(os.path.join(HERE, "diff_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print("wrote diff_report.json")
    sys.exit(0 if (ok and fuzz_diff == 0) else 1)


if __name__ == "__main__":
    main()
