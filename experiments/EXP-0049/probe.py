#!/usr/bin/env python3
"""EXP-0049 drift re-audit probe (READ-ONLY vs repo; CPU-only, deterministic).

Static checks + behavioral probes comparing notebooks/submit_gold/submit_gold.ipynb
(core cell exec'd in isolation with stub constants) against scripts/dog_detect.py
and scripts/baseline_link.py on identical inputs. Writes metrics.json.
"""
import ast
import json
import os
import random
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NB_PATH = os.path.join(ROOT, "notebooks", "submit_gold", "submit_gold.ipynb")
META_PATH = os.path.join(ROOT, "notebooks", "submit_gold", "kernel-metadata.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "metrics.json")

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import numpy as np  # noqa: E402
import zarr  # noqa: E402
from dog_detect import detect as repo_detect  # noqa: E402
import baseline_link as BL  # noqa: E402

results = {"experiment": "EXP-0049", "static": {}, "probes": {}, "verdict": None,
           "elapsed_s": 0.0}
t_all = time.time()
ok_all = True


def record(section, name, passed, detail=""):
    global ok_all
    results[section][name] = {"equal": bool(passed), "detail": str(detail)}
    if not passed:
        ok_all = False
    print(f"[{'PASS' if passed else 'FAIL'}] {section}/{name} {detail}", flush=True)


# ---------- 1. static checks ----------
nb = json.load(open(NB_PATH))
code_cells = [(i, "".join(c["source"])) for i, c in enumerate(nb["cells"])
              if c["cell_type"] == "code"]
full = "\n".join(s for _, s in code_cells)

n_gate7 = len(re.findall(r"GATE_UM\s*=\s*7\.0", full))
n_10 = len(re.findall(r"10\.0", full))
record("static", "gate_um_single_7_no_10",
       n_gate7 == 1 and n_10 == 0, f"GATE_UM=7.0 x{n_gate7}, '10.0' x{n_10}")

has_fw = "def find_wheels" in full and "os.walk" in full
hardcoded = ("biohub-zarr-wheels" in full) or ("wheels/" in full.lower()
             .replace("find_wheels", "").replace(".whl", "")) or bool(
    re.search(r'WHEELS\s*=\s*["\']', full))
record("static", "find_wheels_search_based_no_hardcoded",
       has_fw and not hardcoded, f"def+walk={has_fw}, hardcoded={hardcoded}")

compile_ok, bad = True, []
for i, src in code_cells:
    try:
        ast.parse(src)
    except SyntaxError as e:
        compile_ok, bad = False, bad + [f"cell{i}:{e}"]
record("static", "all_code_cells_compile",
       compile_ok, f"{len(code_cells)} code cells" + (f" BAD={bad}" if bad else ""))

meta = json.load(open(META_PATH))
m_ok = (meta.get("enable_gpu") is False and meta.get("enable_internet") is False
        and bool(meta.get("dataset_sources")) and bool(meta.get("competition_sources")))
record("static", "kernel_metadata_flags",
       m_ok, f"gpu={meta.get('enable_gpu')} net={meta.get('enable_internet')} "
       f"ds={meta.get('dataset_sources')} comp={meta.get('competition_sources')}")

pct_ok = ('"44b6": 99.0' in full and '"6bba": 98.5' in full
          and "PCT_DEFAULT = 98.5" in full)
fork_tokens = ["fork", "two-phase", "two_phase", "phased", "_split",
               "prominence", "split_size", "split("]
# allowlist: str.split on sample names only
tmp = full.replace('name.split', 'name.SPLIT')
fork_hit = [t for t in fork_tokens if t in tmp]
record("static", "pct_map_and_no_forks",
       pct_ok and not fork_hit, f"pct_map={pct_ok}, fork_tokens={fork_hit or 'none'}")

# ---------- 2a. exec notebook core cell in isolation ----------
core_src = "".join(nb["cells"][3]["source"])
ns = {"np": np, "VOXEL": (1.625, 0.40625, 0.40625),
      "SIG_SMALL": (1.0, 3.0, 3.0), "SIG_LARGE": (1.6, 5.0, 5.0),
      "MIN_SIZE": 50, "GATE_UM": 7.0}
exec(compile(core_src, "nb_core_cell", "exec"), ns)  # noqa: S102 (local audit)
nb_detect, nb_link, nb_assign = ns["detect_frame"], ns["link_frames"], ns["assign"]

# ---------- 2b. detect equivalence on 6 frames ----------
detect_cases = ([("6bba_05b6850b", t, 98.5) for t in (20, 21, 22)]
                + [("44b6_0113de3b", t, 99.0) for t in (20, 21, 22)])
frames_cache = {}
det_all_eq, det_detail = True, []
for sid, t, pct in detect_cases:
    vol = zarr.open_group(os.path.join(ROOT, "data", "train", f"{sid}.zarr"),
                          mode="r")["0"][t]
    t0 = time.time()
    nb_pos = nb_detect(vol, pct)
    repo_nodes, _ = repo_detect(vol, pct=pct)  # repo defaults: min_size 50, DoG sigmas, no split
    repo_pos = sorted([(z, y, x) for z, y, x, _sp, _pa in repo_nodes])
    frames_cache.setdefault((sid, pct), {})[t] = nb_pos
    eq = nb_pos == repo_pos
    det_all_eq &= eq
    det_detail.append(f"{sid} t{t} pct={pct} n={len(nb_pos)} eq={eq} "
                      f"({time.time()-t0:.0f}s)")
    if not eq:
        for a, b in zip(nb_pos, repo_pos):
            if a != b:
                det_detail.append(f"  first diff nb={a} repo={b}")
                break
record("probes", "detect_positions_equal_6_frames",
       det_all_eq, "; ".join(det_detail))

# ---------- 2c. link equivalence on both 3-frame chains ----------
link_all_eq, link_detail = True, []
for sid, pct in [("6bba_05b6850b", 98.5), ("44b6_0113de3b", 99.0)]:
    frames = [frames_cache[(sid, pct)][t] for t in (20, 21, 22)]
    nb_nodes, nb_edges = nb_link(frames)
    gt_nodes, gid = [], 0  # frame-major ids, identical enumeration order as notebook
    for t, cents in enumerate(frames):
        for (z, y, x) in cents:
            gid += 1
            gt_nodes.append({"id": gid, "t": t, "z": z, "y": y, "x": x})
    pred = BL.link({"nodes": gt_nodes, "edges": []}, maxd=7.0)
    eq = (sorted(map(tuple, pred["edges"])) == sorted(map(tuple, nb_edges))
          and len(nb_nodes) == len(gt_nodes))
    link_all_eq &= eq
    link_detail.append(f"{sid} nodes={len(nb_nodes)} nb_edges={len(nb_edges)} "
                       f"repo_edges={len(pred['edges'])} eq={eq}")
record("probes", "linked_edges_equal_2_chains_maxd7",
       link_all_eq, "; ".join(link_detail))

# ---------- 2d. assign equivalence incl scipy path (N=70) ----------
rng = random.Random(0)
N = 70
C = [[rng.random() * 10.0 for _ in range(N)] for _ in range(N)]
a_nb = nb_assign([row[:] for row in C])
a_repo = BL._assign([row[:] for row in C])
def cost_of(a):
    return sum(C[i][j] for i, j in enumerate(a) if 0 <= j < N)
eq_assign = a_nb == a_repo
record("probes", "assign_equal_scipy_path_N70",
       eq_assign, f"identical_perm={eq_assign} cost={cost_of(a_repo):.6f} "
       f"repo_backend={BL._assign.backend}")
C5 = [[rng.random() * 10.0 for _ in range(5)] for _ in range(5)]
eq5 = nb_assign([r[:] for r in C5]) == BL._assign([r[:] for r in C5])
record("probes", "assign_equal_pure_path_N5",
       eq5, f"identical_perm={eq5} repo_backend={BL._assign.backend}")

results["verdict"] = "IN-SYNC" if ok_all else "DRIFTED"
results["elapsed_s"] = round(time.time() - t_all, 1)
json.dump(results, open(OUT_PATH, "w"), indent=2)
print(f"VERDICT: {results['verdict']} ({results['elapsed_s']}s) -> {OUT_PATH}")
sys.exit(0 if ok_all else 1)
