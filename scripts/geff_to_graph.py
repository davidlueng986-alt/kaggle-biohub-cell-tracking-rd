#!/usr/bin/env python3
"""Read .geff (Zarr v3) into score.py JSON graphs (stdlib+numpy+zarr).

Usage:
  python3 scripts/geff_to_graph.py data/train/SAMPLE.geff [--out graph.json]
  python3 scripts/geff_to_graph.py --all data/train --out-dir experiments/EXP-0003/gt

Output per sample: {"nodes":[{id,t,z,y,x}...], "edges":[[u,v]...],
"T_true": estimated_number_of_nodes, "voxel_size_um":[1.625,0.40625,0.40625],
"sample": id, "embryo": prefix}
T_true source: root attrs .geff.estimated_number_of_nodes (fallback: scan
common keys; if missing -> null with T_true_missing flag).
"""
import json
import pathlib
import sys

VOXEL = [1.625, 0.40625, 0.40625]


def read_geff(path):
    import zarr
    g = zarr.open_group(str(path), mode="r")
    ids = [int(v) for v in g["nodes/ids"][:].tolist()]
    t = [int(v) for v in g["nodes/props/t/values"][:].tolist()]
    z = [int(v) for v in g["nodes/props/z/values"][:].tolist()]
    y = [int(v) for v in g["nodes/props/y/values"][:].tolist()]
    x = [int(v) for v in g["nodes/props/x/values"][:].tolist()]
    edges = [[int(u), int(v)] for u, v in g["edges/ids"][:].tolist()]
    nodes = [{"id": i, "t": tt, "z": zz, "y": yy, "x": xx}
             for i, tt, zz, yy, xx in zip(ids, t, z, y, x)]
    attrs = json.loads(json.dumps(dict(g.attrs)))
    T = None
    geff = attrs.get("geff", {})
    for k in ("estimated_number_of_nodes", "estimatedNumberOfNodes",
              "n_nodes_estimate", "t_true"):
        if k in geff:
            T = int(geff[k])
            break
        if k in attrs:
            T = int(attrs[k])
            break
    # deep search one level
    if T is None:
        def hunt(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "estimated_number_of_nodes":
                        return int(v)
                    r = hunt(v)
                    if r is not None:
                        return r
            return None
        T = hunt(attrs)
    return {"nodes": nodes, "edges": edges, "T_true": T,
            "voxel_size_um": VOXEL, "T_true_missing": T is None}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("geff", nargs="?", help=".geff path")
    ap.add_argument("--out", help="output JSON path")
    ap.add_argument("--all", dest="all_dir",
                    help="convert every *.geff under DIR")
    ap.add_argument("--out-dir", help="output dir for --all")
    a = ap.parse_args(argv)
    if a.all_dir:
        assert a.out_dir, "--out-dir required with --all"
        out = pathlib.Path(a.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        ids = sorted(p.name[:-5] for p in
                     pathlib.Path(a.all_dir).glob("*.geff"))
        for sid in ids:
            gr = read_geff(pathlib.Path(a.all_dir) / f"{sid}.geff")
            gr["sample"] = sid
            gr["embryo"] = sid.split("_")[0]
            (out / f"{sid}_gt.json").write_text(json.dumps(gr))
            print(f"{sid}: n={len(gr['nodes'])} e={len(gr['edges'])} "
                  f"T_true={gr['T_true']}")
        return 0
    assert a.geff, "provide .geff path or --all DIR"
    gr = read_geff(a.geff)
    s = json.dumps(gr, indent=1)
    if a.out:
        pathlib.Path(a.out).write_text(s)
        print(f"wrote {a.out} n={len(gr['nodes'])}")
    else:
        print(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
