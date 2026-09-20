#!/usr/bin/env python3
"""Graphs -> submission.csv writer + format checker (GOLD §5 submit path).

Verified schema (docs/COMPETITION.md 2026-09-09):
  id,dataset,row_type,node_id,t,z,y,x,source_id,target_id
  node rows: node_id,t,z,y,x set; source/target = -1
  edge rows: source/target set; node_id,t,z,y,x = -1
  id: consecutive ints from 0; every test dataset present.

Usage:
  python3 scripts/graphs_to_csv.py --pred-dir DIR --out submission.csv
    (DIR contains <dataset>_pred.json graphs as emitted by baseline_link.py)
  python3 scripts/graphs_to_csv.py --check submission.csv [--expect-datasets a,b]
"""
import csv
import glob
import json
import os
import sys

HEADER = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
          "source_id", "target_id"]


def write_csv(datasets, path):
    """datasets: {name: graph}. Deterministic (sorted).

    AUDIT-FIX C2 (P4): fail loud on empty datasets. A graph with no nodes
    and no edges would previously vanish from the CSV (zero rows), silently
    breaking the "every test dataset present" schema. An empty datasets
    dict (header-only file) fails the same way.
    """
    if not datasets:
        raise ValueError("write_csv: no datasets (would write header-only CSV)")
    empty = sorted(n for n, g in datasets.items()
                   if not g.get("nodes") and not g.get("edges"))
    if empty:
        raise ValueError(
            f"write_csv: empty dataset(s) {empty} have no nodes/edges and "
            "would silently vanish from the CSV; fix the upstream graph or "
            "drop the dataset explicitly")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        i = 0
        for name in sorted(datasets):
            g = datasets[name]
            for n in sorted(g["nodes"], key=lambda d: d["id"]):
                w.writerow([i, name, "node", n["id"], n["t"], n["z"], n["y"],
                            n["x"], -1, -1])
                i += 1
            for u, v in sorted(map(tuple, g["edges"])):
                w.writerow([i, name, "edge", -1, -1, -1, -1, -1, u, v])
                i += 1
    return i


def check(path, expect=None):
    errs = []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return ["empty file"]
    ids = [int(r["id"]) for r in rows]
    if ids != list(range(len(rows))):
        errs.append("id column not consecutive 0..N-1")
    seen_ds = set()
    node_ids = {}
    # AUDIT-FIX C2 (P4): fail loud on duplicate node ids within a dataset.
    # Previously node ids collapsed into a set, so dup ids passed silently
    # and edge-ref validation ran against the collapsed set.
    dup_ids = set()
    for r in rows:
        seen_ds.add(r["dataset"])
        if r["row_type"] == "node":
            if (r["source_id"], r["target_id"]) != ("-1", "-1"):
                errs.append(f"node row {r['id']}: source/target must be -1")
            try:
                nid = int(r["node_id"])
                known = node_ids.setdefault(r["dataset"], set())
                if nid in known:
                    dup_ids.add((r["dataset"], nid))
                known.add(nid)
                for k in ("t", "z", "y", "x"):
                    int(r[k])
            except ValueError:
                errs.append(f"node row {r['id']}: bad int coords")
        elif r["row_type"] == "edge":
            if (r["node_id"], r["t"], r["z"], r["y"], r["x"]) != ("-1",) * 5:
                errs.append(f"edge row {r['id']}: node/t/z/y/x must be -1")
            try:
                int(r["source_id"]); int(r["target_id"])
            except ValueError:
                errs.append(f"edge row {r['id']}: bad edge refs")
        else:
            errs.append(f"row {r['id']}: bad row_type {r['row_type']!r}")
    # edge refs must exist as nodes (per dataset)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r["row_type"] == "edge":
                known = node_ids.get(r["dataset"], set())
                if int(r["source_id"]) not in known or \
                        int(r["target_id"]) not in known:
                    errs.append(f"edge row {r['id']}: dangling ref")
                    break
    for ds, nid in sorted(dup_ids):
        errs.append(f"dataset {ds}: duplicate node id {nid}")
    if expect and set(expect) - seen_ds:
        errs.append(f"missing datasets: {sorted(set(expect) - seen_ds)}")
    return errs


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-dir")
    ap.add_argument("--out")
    ap.add_argument("--check")
    ap.add_argument("--expect-datasets", default="")
    a = ap.parse_args(argv)
    if a.check:
        errs = check(a.check, a.expect_datasets.split(",") if a.expect_datasets else None)
        if errs:
            print("INVALID:", *errs, sep="\n  ")
            return 1
        print(f"submission.csv OK "
              f"({sum(1 for _ in open(a.check)) - 1} rows)")
        return 0
    assert a.pred_dir and a.out, "--pred-dir + --out required"
    ds = {}
    src_of = {}
    for p in sorted(glob.glob(os.path.join(a.pred_dir, "*_pred.json"))):
        name = os.path.basename(p)[:-len("_pred.json")]
        if name.startswith("r10_"):
            # AUDIT-FIX C2 (P4): the r10_ strip used to last-write-win on
            # collision (r10_foo + foo -> foo, silently dropping one graph).
            # Fail loud instead; solver/output naming itself is unchanged.
            name = name[4:]
        if name in ds:
            raise ValueError(
                f"dataset name collision: {p} and {src_of[name]} both map "
                f"to {name!r}; rename inputs so names are unique")
        src_of[name] = p
        ds[name] = json.load(open(p))
    n = write_csv(ds, a.out)
    print(f"wrote {a.out}: {len(ds)} datasets, {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
