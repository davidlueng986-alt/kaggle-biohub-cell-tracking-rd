#!/usr/bin/env python3
"""EXP-0059 step 1: GT-free brightness proxy + frozen-rule assignments.

B(S) = mean raw intensity over frames t20-29. Rule (frozen in hypothesis.md):
fit-median split; B <= median -> pct 96.0 else 99.0. Gate always 7.0.
LOSO: fit median on other 5. Nested: fit median on embryo A, apply to B.
"""
import json
import os
import statistics

import numpy as np
import zarr

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_TRAIN = "/home/box/workspace/kaggle-biohub-rd/data/train"
SAMPLES = [
    ("44b6_0113de3b", "44b6"), ("44b6_0b24845f", "44b6"),
    ("44b6_0c582fdc", "44b6"), ("6bba_05b6850b", "6bba"),
    ("6bba_05db0fb1", "6bba"), ("6bba_062c8d37", "6bba"),
]
FRAMES = list(range(20, 30))
LOW, HIGH = 96.0, 99.0


def brightness(sid):
    Z = zarr.open_group(os.path.join(DATA_TRAIN, f"{sid}.zarr"), mode="r")["0"]
    ms = [float(np.asanyarray(Z[t]).mean()) for t in FRAMES]
    return sum(ms) / len(ms), ms


def assign(b, med):
    return LOW if b <= med else HIGH


def main():
    B = {}
    for sid, _ in SAMPLES:
        mean, per_frame = brightness(sid)
        B[sid] = mean
        print(f"{sid}: B={mean:.4f} (per-frame {[f'{m:.2f}' for m in per_frame]})", flush=True)
    out = {"B": B, "frames": FRAMES, "low": LOW, "high": HIGH, "loso": {}, "nested": {}}
    for sid, _ in SAMPLES:
        fit = sorted(B[s] for s, _ in SAMPLES if s != sid)
        med = statistics.median(fit)
        out["loso"][sid] = {
            "fit_on": sorted(s for s, _ in SAMPLES if s != sid),
            "fit_median": med,
            "B_holdout": B[sid],
            "assigned_pct": assign(B[sid], med),
            "gate": 7.0,
        }
        print(f"LOSO holdout {sid}: fit_median={med:.4f} B={B[sid]:.4f} -> pct {assign(B[sid], med)}", flush=True)
    for emb in ("44b6", "6bba"):
        fit_ids = [s for s, e in SAMPLES if e == emb]
        test_ids = [s for s, e in SAMPLES if e != emb]
        med = statistics.median([B[s] for s in fit_ids])
        for sid in test_ids:
            out["nested"][sid] = {
                "fit_embryo": emb, "fit_on": sorted(fit_ids),
                "fit_median": med, "B_holdout": B[sid],
                "assigned_pct": assign(B[sid], med), "gate": 7.0,
            }
        amap = {s: assign(B[s], med) for s in test_ids}
        print(f"nested fit={emb} median={med:.4f} -> held-out {emb != '44b6' and '44b6' or '6bba'}: {amap}", flush=True)
    with open(os.path.join(HERE, "brightness.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote brightness.json")


if __name__ == "__main__":
    main()
