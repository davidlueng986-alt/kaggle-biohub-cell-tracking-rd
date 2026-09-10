#!/usr/bin/env python3
"""EXP-0032 verification: spot-checks + metrics.json.

Checks (deterministic, seed 7):
  1. 20 random positives: center-box mean > full-patch mean (bright blob test).
  2. Positives vs negatives differ statistically (center-box mean intensity).
  3. Manifest <-> .npy row alignment, counts, balance, disk size.
Writes experiments/EXP-0032/metrics.json.
"""
import csv
import json
import pathlib
import time

import numpy as np
from scipy import stats as sstats

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "EXP-0032"
PATCH_DIR = ROOT / "data" / "patches"
CZ, CY, CX = 8, 16, 16  # center box: middle (8,16,16) of (16,48,48)


def center_mean(p):
    z0, y0, x0 = (16 - CZ) // 2, (48 - CY) // 2, (48 - CX) // 2
    return float(p[z0:z0 + CZ, y0:y0 + CY, x0:x0 + CX].mean())


def main():
    t0 = time.time()
    rng = np.random.default_rng(7)
    rows = list(csv.DictReader(open(PATCH_DIR / "MANIFEST.csv")))
    by_split = {}
    for r in rows:
        by_split.setdefault(r["split"], []).append(r)

    per_split, pos_c, neg_c, neg_bright = {}, [], [], []
    check20_pass = 0
    check20_detail = []
    for split in sorted(by_split):
        arr = np.load(PATCH_DIR / split / "patches.npy", mmap_mode="r")
        rs = by_split[split]
        assert len(rs) == arr.shape[0], f"{split}: manifest {len(rs)} vs npy {arr.shape[0]}"
        assert arr.shape[1:] == (16, 48, 48), arr.shape
        for i, r in enumerate(rs):  # manifest order == patch row order
            assert int(r["idx_in_split"]) == i
        pos_idx = [i for i, r in enumerate(rs) if r["label"] == "1"]
        neg_idx = [i for i, r in enumerate(rs) if r["label"] == "0"]
        # node_id back-reference sanity on 5 random positives
        for i in rng.choice(pos_idx, size=min(5, len(pos_idx)), replace=False):
            assert int(rs[i]["node_id"]) >= 0 and rs[i]["neg_type"] == ""
        cm = np.array([center_mean(arr[i]) for i in range(arr.shape[0])])
        fm = np.array([float(arr[i].mean()) for i in range(arr.shape[0])])
        pos_c.extend(cm[pos_idx].tolist())
        neg_c.extend(cm[neg_idx].tolist())
        nb = sum(1 for i in neg_idx if rs[i]["neg_type"] == "bright_max")
        neg_bright.append(nb)
        # 20-random-positive bright-blob test (per split: up to 20)
        k = min(20, len(pos_idx))
        for i in rng.choice(pos_idx, size=k, replace=False):
            ok = bool(cm[i] > fm[i])
            check20_pass += ok
            if len(check20_detail) < 20:
                check20_detail.append({"split": split, "idx": int(i),
                                       "center_mean": round(cm[i], 1),
                                       "full_mean": round(fm[i], 1), "pass": ok})
        per_split[split] = {"n": len(rs), "pos": len(pos_idx), "neg": len(neg_idx),
                            "neg_bright_max": nb,
                            "neg_random_bg": len(neg_idx) - nb}
        check20_total_split = k

    pos_c = np.array(pos_c)
    neg_c = np.array(neg_c)
    tstat, pval = sstats.ttest_ind(pos_c, neg_c, equal_var=False)
    n20 = sum(min(20, v["pos"]) for v in per_split.values())
    size_b = sum(p.stat().st_size for p in PATCH_DIR.rglob("*.npy"))
    size_b += (PATCH_DIR / "MANIFEST.csv").stat().st_size

    metrics = {
        "exp_id": "EXP-0032",
        "title": "Training patch export",
        "status": "done",
        "n_patches_total": len(rows),
        "n_pos": int((pos_c.shape[0])),
        "n_neg": int((neg_c.shape[0])),
        "balance_pos_frac": round(float(len(pos_c) / len(rows)), 4),
        "per_split": per_split,
        "patch_shape_zyx": [16, 48, 48],
        "dtype": "uint16",
        "disk_bytes": size_b,
        "disk_mb": round(size_b / 1e6, 1),
        "spotcheck_20pos_center_gt_full": f"{check20_pass}/{n20}",
        "pos_center_mean": round(float(pos_c.mean()), 1),
        "pos_center_std": round(float(pos_c.std()), 1),
        "neg_center_mean": round(float(neg_c.mean()), 1),
        "neg_center_std": round(float(neg_c.std()), 1),
        "welch_t": round(float(tstat), 2),
        "welch_p": float(pval),
        "verify_s": round(time.time() - t0, 1),
        "seed_export": 0,
        "seed_verify": 7,
        "check20_sample": check20_detail,
        "protocol": "v1.1 (enabling rung; no trusted-scorer promotion claim)",
    }
    (EXP / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: v for k, v in metrics.items() if k != "check20_sample"}, indent=2))


if __name__ == "__main__":
    main()
