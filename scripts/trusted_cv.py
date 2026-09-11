#!/usr/bin/env python3
"""Trusted CV harness (PROTOCOL v1.2, FROZEN).

LOSO + embryo-nested with nested hyperparameters. Scorer v1.1.0 unchanged.
Default grid: DoG pct {96,97,98,98.5,99,99.5} x link gate {7,10} (link-only,
no forks unless declared). Fit = argmax trusted micro score on FIT samples
only; tie-break (deterministic): higher micro, then FEWER total detections
(count discipline), then smaller gate, then higher pct.

Detection cache: frozen full-video artifacts are reused by manifest (no file
moves); missing (sample,pct) combos are detected on demand into --det-cache
with the dog_detect.py CLI schema. Linking reassigns global ids per video
(det files restart ids per frame). All micro-averaging reuses
score.score_samples for exact v1.1 semantics.

Usage:
  python3 scripts/trusted_cv.py --smoke [--out metrics.json]
  python3 scripts/trusted_cv.py --full [--out metrics.json] [--det-cache DIR]
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score import score_samples  # noqa: E402
import baseline_link as BL  # noqa: E402
from dog_detect import detect as dog_detect_fn  # noqa: E402

PROTOCOL_VERSION = "1.2"
SCORER_VERSION = "1.1.0"
VOXEL = (1.625, 0.40625, 0.40625)
DATA_TRAIN = "/home/box/workspace/kaggle-biohub-rd/data/train"
GT_DIR = "/home/box/workspace/kaggle-biohub-rd/experiments/EXP-0003/gt"
EXP_DIR = "/home/box/workspace/kaggle-biohub-rd/experiments"

SAMPLES = [
    ("44b6_0113de3b", "44b6"), ("44b6_0b24845f", "44b6"),
    ("44b6_0c582fdc", "44b6"), ("6bba_05b6850b", "6bba"),
    ("6bba_05db0fb1", "6bba"), ("6bba_062c8d37", "6bba"),
]
GRID_PCT = [96.0, 97.0, 98.0, 98.5, 99.0, 99.5]
GRID_GATE = [7.0, 10.0]

# Frozen full-video detection artifacts: (sid, pct) -> (dir, stem).
# Verified against EXP rows at build time; missing combos detected on demand.
DET_MANIFEST = {
    ("44b6_0113de3b", 99.0): ("EXP-0008", "full_44b6_0113de3b"),
    ("44b6_0113de3b", 98.5): ("EXP-0009", "full_44b6_0113de3b"),
    ("6bba_05b6850b", 99.0): ("EXP-0008", "full_6bba_05b6850b"),
    ("6bba_05b6850b", 98.5): ("EXP-0009", "full_6bba_05b6850b"),
    ("44b6_0b24845f", 99.0): ("EXP-0021", "full_44b6_0b24845f"),
    ("44b6_0c582fdc", 99.0): ("EXP-0021", "full_44b6_0c582fdc"),
    ("6bba_05db0fb1", 98.5): ("EXP-0021", "full_6bba_05db0fb1"),
    ("6bba_062c8d37", 98.5): ("EXP-0021", "full_6bba_062c8d37"),
    ("6bba_05db0fb1", 96.0): ("EXP-0039", "full_6bba_05db0fb1"),
    ("44b6_0b24845f", 96.0): ("EXP-0040", "full_44b6_0b24845f"),
    ("44b6_0c582fdc", 96.0): ("EXP-0040", "full_44b6_0c582fdc"),
}


def load_gt(sid):
    with open(os.path.join(GT_DIR, f"{sid}_gt.json")) as f:
        return json.load(f)


def det_path_for(sid, pct, cache_dir):
    """Resolve det JSON path for frame t via manifest or cache (detect if missing)."""
    if (sid, pct) in DET_MANIFEST:
        exp, stem = DET_MANIFEST[(sid, pct)]
        return os.path.join(EXP_DIR, exp, stem + "_t{t}.json"), True
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{sid}_p{pct}_t{{t}}.json"), False


def ensure_det(sid, pct, cache_dir, frames=range(100)):
    import zarr
    path_t, frozen = det_path_for(sid, pct, cache_dir)
    missing = [t for t in frames
               if not (os.path.exists(path_t.format(t=t)))]
    if missing and frozen:
        raise FileNotFoundError(f"frozen det missing frames for {(sid, pct)}: {missing[:5]}")
    if missing:
        Z = zarr.open_group(os.path.join(DATA_TRAIN, f"{sid}.zarr"), mode="r")["0"]
        for t in missing:
            nodes, params = dog_detect_fn(__import__("numpy").asarray(Z[t]), pct=pct)
            out = {"nodes": [{"id": i + 1, "t": t, "z": z, "y": y, "x": x}
                             for i, (z, y, x, _, _) in enumerate(nodes)]}
            out["params"] = params
            with open(path_t.format(t=t), "w") as f:
                json.dump(out, f)
    return path_t


def load_nodes(sid, pct, cache_dir, frames=range(100)):
    path_t = ensure_det(sid, pct, cache_dir, frames)
    nodes, gid = [], 0
    for t in frames:
        with open(path_t.format(t=t)) as f:
            det = json.load(f)
        for n in det["nodes"]:
            gid += 1
            nodes.append({"id": gid, "t": t, "z": n["z"], "y": n["y"], "x": n["x"]})
    return nodes, gid


def link_and_score(sid, pct, gate, cache_dir, gt_cache):
    """Link cached/fresh detections with gate; score vs GT. Returns (pred, result)."""
    nodes, n_det = load_nodes(sid, pct, cache_dir)
    pred = BL.link({"nodes": nodes, "edges": []}, maxd=gate)
    gt = gt_cache[sid]
    agg = score_samples([(sid, pred, gt, None)])
    s = agg["per_sample"][0]
    return pred, {"edge": s["adjusted_edge_jaccard"], "raw": s["edge_jaccard_raw"],
                  "div": s["division_jaccard"], "score": s["score"],
                  "ec": s["edge_counts"], "dc": s["division_counts"],
                  "n_det": n_det, "assign": pred.get("assign"),
                  "T_true": s["T_true"]}


def fit_best(fit_sids, grid, cache, gt_cache):
    """Argmax trusted micro score on fit samples only. Returns (cfg, table)."""
    table = []
    for pct, gate in grid:
        num = den = 0.0
        dTP = dFP = dFN = 0
        n_det = 0
        for sid in fit_sids:
            r = cache[(sid, pct, gate)]
            c = r["ec"]
            w = c["TP"] + c["FP"] + c["FN"]
            num += r["edge"] * w
            den += w
            d = r["dc"]
            dTP += d["TP"]
            dFP += d["FP"]
            dFN += d["FN"]
            n_det += r["n_det"]
        micro_edge = num / den if den else 0.0
        dden = dTP + dFP + dFN
        micro_div = 1.0 if dden == 0 else dTP / dden
        table.append({"pct": pct, "gate": gate, "micro_edge": micro_edge,
                      "micro_div": micro_div, "score": micro_edge + 0.1 * micro_div,
                      "n_det": n_det})
    table.sort(key=lambda r: (-r["score"], r["n_det"], r["gate"], -r["pct"]))
    best = table[0]
    return (best["pct"], best["gate"]), table


def run_cv(samples, grid, cache_dir, gt_cache, verbose=True):
    t0 = time.time()
    # Phase 1: per-(sample,config) link+score, computed once, reused by all folds.
    cache = {}
    cfgs = [(p, g) for p in grid[0] for g in grid[1]]
    for sid, _ in samples:
        for pct, gate in cfgs:
            _, r = link_and_score(sid, pct, gate, cache_dir, gt_cache)
            cache[(sid, pct, gate)] = r
            if verbose:
                print(f"  [cache] {sid} p{pct} g{gate}: edge={r['edge']:.4f} "
                      f"ec={r['ec']['TP']}/{r['ec']['FP']}/{r['ec']['FN']} "
                      f"det={r['n_det']}", flush=True)
    # Phase 2a: LOSO.
    loso_rows = {}
    for sid, _ in samples:
        fit = [s for s, _ in samples if s != sid]
        (bp, bg), ftable = fit_best(fit, cfgs, cache, gt_cache)
        r = cache[(sid, bp, bg)]
        loso_rows[sid] = {"fitted_pct": bp, "fitted_gate": bg,
                           "fit_on": fit, "fit_winner_score": ftable[0]["score"],
                           "edge": r["edge"], "raw": r["raw"], "div": r["div"],
                           "score": r["score"], "ec": r["ec"], "dc": r["dc"],
                           "n_det": r["n_det"]}
        if verbose:
            print(f"  [loso] holdout {sid}: HP=({bp},{bg}) edge={r['edge']:.4f} "
                  f"score={r['score']:.4f}", flush=True)
    # Phase 2b: embryo-nested (fit on embryo A samples, score embryo B).
    embryos = sorted({e for _, e in samples})
    nested = {}
    for hold in embryos:
        fit = [s for s, e in samples if e != hold]
        test = [s for s, e in samples if e == hold]
        (bp, bg), _ = fit_best(fit, cfgs, cache, gt_cache)
        num = den = 0.0
        per = {}
        for sid in test:
            r = cache[(sid, bp, bg)]
            c = r["ec"]
            w = c["TP"] + c["FP"] + c["FN"]
            num += r["edge"] * w
            den += w
            per[sid] = {"edge": r["edge"], "score": r["score"], "ec": r["ec"]}
        nested[hold] = {"HP": [bp, bg], "fit_on": fit,
                        "micro": num / den if den else 0.0, "per_sample": per}
        if verbose:
            print(f"  [nested] holdout {hold}: HP=({bp},{bg}) "
                  f"micro={nested[hold]['micro']:.4f}", flush=True)
    # Phase 3: aggregates with exact micro semantics (recomputed from held-out pairs).
    def micro_of(rows):
        num = den = 0.0
        for v in rows.values():
            c = v["ec"]
            w = c["TP"] + c["FP"] + c["FN"]
            num += v["edge"] * w
            den += w
        return num / den if den else 0.0
    loso_micro = micro_of(loso_rows)
    loso_worst = min(v["score"] for v in loso_rows.values())
    nested_worst = min(v["micro"] for v in nested.values())
    return {
        "protocol_version": PROTOCOL_VERSION,
        "cv_tag": "trusted",
        "scorer_version": SCORER_VERSION,
        "grid": {"pct": grid[0], "gate": grid[1]},
        "loso_micro": loso_micro,
        "loso_worst": loso_worst,
        "embryo_nested_worst": nested_worst,
        "loso_table": loso_rows,
        "embryo_nested": nested,
        "elapsed_s": round(time.time() - t0, 1),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Trusted CV harness (PROTOCOL v1.2)")
    ap.add_argument("--smoke", action="store_true",
                    help="2-sample dry run (one per embryo, tiny grid)")
    ap.add_argument("--full", action="store_true",
                    help="full 6-sample rebaseline (default grid)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--det-cache", default=None)
    args = ap.parse_args(argv)
    if args.smoke:
        samples = [SAMPLES[0], SAMPLES[3]]
        grid = ([98.5, 99.0], [7.0])
        cache_dir = args.det_cache or "/tmp/trusted_cv_smoke"
    else:
        samples = SAMPLES
        grid = (GRID_PCT, GRID_GATE)
        cache_dir = args.det_cache or "det_cache"
    os.makedirs(cache_dir, exist_ok=True)
    gt_cache = {sid: load_gt(sid) for sid, _ in samples}
    res = run_cv(samples, grid, cache_dir, gt_cache)
    print(json.dumps({k: v for k, v in res.items()
                      if k in ("cv_tag", "loso_micro", "loso_worst",
                               "embryo_nested_worst", "elapsed_s")}, indent=2))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
