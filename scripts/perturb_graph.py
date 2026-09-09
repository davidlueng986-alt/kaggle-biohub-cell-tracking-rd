#!/usr/bin/env python3
"""Perturb graph node coordinates with seeded sub-voxel jitter (EXP-0006).

Simulates detection noise to test linker stability. Jitter σ=0.3 voxel
isotropic (≈0.49um z, 0.12um y/x — far below the 7um matching gate, so GT
node identity is preserved; only proposal-boundary distances can flicker).

Usage: python3 scripts/perturb_graph.py gt.json --seed 0 --out jit.json
Deterministic per seed. Edges/ids/T_true untouched.
"""
import json
import sys

SIGMA_VOX = 0.3


def perturb(gt, seed, sigma=SIGMA_VOX):
    import random
    rng = random.Random(seed)
    nodes = []
    for n in gt["nodes"]:
        nodes.append({"id": n["id"], "t": n["t"],
                      "z": n["z"] + rng.gauss(0, sigma),
                      "y": n["y"] + rng.gauss(0, sigma),
                      "x": n["x"] + rng.gauss(0, sigma)})
    g = {"nodes": nodes, "edges": [list(e) for e in gt["edges"]],
         "T_true": gt.get("T_true"), "voxel_size_um": gt.get("voxel_size_um"),
         "jitter_seed": seed, "jitter_sigma_vox": sigma}
    return g


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("gt")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--sigma", type=float, default=SIGMA_VOX)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    g = perturb(json.load(open(a.gt)), a.seed, a.sigma)
    json.dump(g, open(a.out, "w"))
    print(f"wrote {a.out} seed={a.seed} sigma={a.sigma}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
