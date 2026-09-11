#!/usr/bin/env python3
"""3D-UNet heatmap cell detector (EXP-0032 patches -> learned detector).

Kernel-safe: imports ONLY torch, numpy, stdlib (offline Kaggle GPU image).
Train: 6bba patches. Validate: detection recall on holdout embryo 44b6.

COORDINATE CONVENTION (from export_patches.py:extract_patch): each patch is
centred on its manifest (z,y,x) full-volume voxel, zero-padded at borders, so
for every positive the GT centroid is ALWAYS the patch-centre voxel
  (PZ//2, PY//2, PX//2) = (8, 24, 24).
Gaussian targets are rendered on the fly at that fixed centre; negatives get
an all-zero target. Manifest (z,y,x) columns are only used for bookkeeping.

Validation reimplements the repo 7um matching rule inline (no repo imports):
  dist_um = sqrt((dz*1.625)^2 + (dy*0.40625)^2 + (dx*0.40625)^2) <= 7.0.

Usage:
  python3 train.py                 # full train (needs patches + GPU for speed)
  python3 train.py --smoke          # CPU smoke: synth fwd/bwd + ckpt + loader
  python3 train.py --epochs 2 --batch-size 8   # quick local run
"""
import argparse
import csv
import os
import pathlib
import random

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

CONFIG = dict(
    seed=0,
    train_split="6bba",          # embryo-grouped CV fold0: train on 6bba ...
    val_split="44b6",            # ... validate on holdout embryo 44b6
    patch_shape=(16, 48, 48),
    patch_center=(8, 24, 24),    # GT centroid convention (see docstring)
    sigma_vox=(1.5, 4.0, 4.0),   # ~1/4 cell radius per train_design.md
    base_ch=32,                  # 3-level UNet -> ~1.4M params
    batch_size=16,
    pos_frac=0.5,                # embryo-balanced: half pos / half neg
    bright_upsample=4.0,         # upweight bright_max negs (44b6 has ~6% hard)
    epochs=20,
    lr=3e-4,
    weight_decay=1e-5,
    peak_thr=0.3,                # heatmap peak -> detection threshold
    match_um=7.0,                # detection matches GT iff within 7 um
    voxel_um=(1.625, 0.40625, 0.40625),
    mine_every=0,                # v9: OFF (zero-collapse escape; HNM's 4x suppressor
                                # deepened the all-zero attractor — triage 2026-09-11; was 2)
    mine_topk=512,               # hardest train negs get boosted weight
    mine_boost=1.0,              # v9: neutral (was 4.0; see mine_every)
    fg_weight=200.0,             # v9: foreground voxel weight in MSE (159 fg vs 36705 bg
                                # voxels/batch makes unweighted MSE + neg-Dice veto lock all-zero;
                                # ~bg/fg ratio; preserves embryo discipline — weights, not data)
    out_dir="/kaggle/working",   # checkpoint dir (falls back to ./working)
)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)  # audit FLAG#5 fix
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def dice_loss(prob, tgt_bin, eps=1e-6):
    """Soft Dice on binarised target (audit FLAG#6: design Opt-A term)."""
    prob = prob.contiguous().view(prob.shape[0], -1)
    tgt_bin = tgt_bin.contiguous().view(tgt_bin.shape[0], -1)
    inter = (prob * tgt_bin).sum(1)
    return (1.0 - (2.0 * inter + eps) / (prob.sum(1) + tgt_bin.sum(1) + eps)).mean()


def find_data_dir():
    import os
    roots = ["/kaggle/input/biohub-train-patches",
             "/kaggle/input/datasets/biohub-train-patches",
             "data/patches",
             str(pathlib.Path(__file__).resolve().parents[2] / "data" / "patches")]
    for c in roots:
        p = pathlib.Path(c) / "MANIFEST.csv"
        if p.is_file():
            return str(p.parent)
    # layout-robust fallback: search for MANIFEST.csv under /kaggle/input
    if os.path.isdir("/kaggle/input"):
        for root, _, files in os.walk("/kaggle/input"):
            if root.count(os.sep) - 4 > 5:
                continue
            if "MANIFEST.csv" in files and "patches.npy" in "".join(files):
                return root
            if "MANIFEST.csv" in files:
                cand = root
                # prefer dirs that also hold patches.npy nearby
                for r2, _, f2 in os.walk(root):
                    if "patches.npy" in f2:
                        return root
                return cand
    import os as _os
    raise FileNotFoundError(
        "MANIFEST.csv not found; /kaggle/input="
        + str(sorted(_os.listdir("/kaggle/input")) if _os.path.isdir("/kaggle/input") else None))


def out_dir():
    d = pathlib.Path(CONFIG["out_dir"])
    try:
        d.mkdir(parents=True, exist_ok=True)
        return d
    except OSError:
        d = pathlib.Path("./working")
        d.mkdir(parents=True, exist_ok=True)
        return d


def gaussian_target():
    """Fixed (16,48,48) Gaussian heatmap at patch centre. Positives only."""
    sh, ct, sg = CONFIG["patch_shape"], CONFIG["patch_center"], CONFIG["sigma_vox"]
    zz, yy, xx = np.mgrid[0:sh[0], 0:sh[1], 0:sh[2]]
    g = (((zz - ct[0]) / sg[0]) ** 2 + ((yy - ct[1]) / sg[1]) ** 2
         + ((xx - ct[2]) / sg[2]) ** 2)
    return np.exp(-0.5 * g).astype(np.float32)


class PatchDataset(Dataset):
    """One embryo split. Backed by np.load(mmap) to stay lean (~471MB uint16).

    Normalisation uses TRAIN-embryo global mean/std only (no val leakage).
    """

    def __init__(self, data_dir, split, gmean=None, gstd=None):
        rows = [r for r in csv.DictReader(open(f"{data_dir}/MANIFEST.csv"))
                if r["split"] == split]
        rows.sort(key=lambda r: int(r["idx_in_split"]))
        self.rows = rows
        self.arr = np.load(f"{data_dir}/{split}/patches.npy", mmap_mode="r")
        assert self.arr.shape[1:] == tuple(CONFIG["patch_shape"]), self.arr.shape
        self.pos_id = np.array([i for i, r in enumerate(rows) if r["label"] == "1"])
        self.neg_id = np.array([i for i, r in enumerate(rows) if r["label"] == "0"])
        self.is_bright = np.array([r["neg_type"] == "bright_max" for r in rows])
        if gmean is None:  # train split: stream stats from memmap (no full load)
            s = np.float64(0)
            s2 = np.float64(0)
            n = np.int64(0)
            for i in range(0, len(rows), 512):
                b = self.arr[i:i + 512].astype(np.float64)
                s += b.sum()
                s2 += (b ** 2).sum()
                n += b.size
            gmean, gstd = s / n, float(np.sqrt(max(s2 / n - (s / n) ** 2, 1e-12)))
        self.gmean, self.gstd = float(gmean), float(gstd)
        self.heat_pos = gaussian_target()
        self.zeros = np.zeros(CONFIG["patch_shape"], dtype=np.float32)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        img = (self.arr[int(i)].astype(np.float32) - self.gmean) / self.gstd
        tgt = self.heat_pos if self.rows[int(i)]["label"] == "1" else self.zeros
        lab = 1.0 if self.rows[int(i)]["label"] == "1" else 0.0
        return (torch.from_numpy(img).unsqueeze(0), torch.from_numpy(tgt).unsqueeze(0),
                torch.tensor(lab, dtype=torch.float32))


class BalancedBatches:
    """Embryo-balanced batch sampler: pos_frac positives + negatives drawn with
    weights (bright_max upweighted xK). Hard-negative hook: set_neg_weights()."""

    def __init__(self, ds, batch_size, pos_frac, bright_upsample, seed, n_batches):
        self.pos = ds.pos_id
        self.neg = ds.neg_id
        self.bs, self.n_pos = batch_size, int(batch_size * pos_frac)
        self.n_batches = n_batches or max(len(ds) // batch_size, 1)
        self.rng = np.random.default_rng(seed)
        base = np.where(ds.is_bright[ds.neg_id], bright_upsample, 1.0)
        self.set_neg_weights(base)  # stores normalised p

    def set_neg_weights(self, w):
        w = np.asarray(w, dtype=np.float64)
        self.neg_p = w / w.sum()

    def __iter__(self):
        for _ in range(self.n_batches):
            b = np.concatenate([
                self.rng.choice(self.pos, size=self.n_pos, replace=True),
                self.rng.choice(self.neg, size=self.bs - self.n_pos,
                                replace=True, p=self.neg_p)])
            self.rng.shuffle(b)
            yield [int(i) for i in b]

    def __len__(self):
        return self.n_batches


class DC(nn.Module):
    def __init__(self, ci, co):
        super().__init__()
        self.n = nn.Sequential(nn.Conv3d(ci, co, 3, padding=1), nn.ReLU(inplace=True),
                               nn.Conv3d(co, co, 3, padding=1), nn.ReLU(inplace=True))

    def forward(self, x):
        return self.n(x)


class UNet(nn.Module):
    """3-level 3D UNet, base 32 ch (~1.4M params). 16x48x48 -> 4x12x12 -> back."""

    def __init__(self, base=32):
        super().__init__()
        self.e0 = DC(1, base)
        self.d0 = nn.MaxPool3d(2)
        self.e1 = DC(base, base * 2)
        self.d1 = nn.MaxPool3d(2)
        self.e2 = DC(base * 2, base * 4)
        self.u1 = nn.ConvTranspose3d(base * 4, base * 2, 2, 2)
        self.c1 = DC(base * 4, base * 2)
        self.u0 = nn.ConvTranspose3d(base * 2, base, 2, 2)
        self.c0 = DC(base * 2, base)
        self.out = nn.Conv3d(base, 1, 1)

    def forward(self, x):
        a0 = self.e0(x)
        a1 = self.e1(self.d0(a0))
        m = self.e2(self.d1(a1))
        u = self.c1(torch.cat([self.u1(m), a1], 1))
        v = self.c0(torch.cat([self.u0(u), a0], 1))
        return self.out(v)


def um_dist(dz, dy, dx):
    vz, vy, vx = CONFIG["voxel_um"]
    return float(np.sqrt((dz * vz) ** 2 + (dy * vy) ** 2 + (dx * vx) ** 2))


@torch.no_grad()
def validate(model, loader, device):
    """Detection recall vs GT centroids on holdout embryo (7um rule, inline)."""
    model.eval()
    cz, cy, cx = CONFIG["patch_center"]
    thr, mu = CONFIG["peak_thr"], CONFIG["match_um"]
    n_pos = n_hit = n_det_neg = n_neg = 0
    errs = []
    for img, _, lab in loader:
        prob = torch.sigmoid(model(img.to(device))).cpu().numpy()
        for h, l in zip(prob, lab.numpy()):
            pk = int(np.argmax(h[0]))
            pz, py, px = np.unravel_index(pk, h[0].shape)
            det = bool(h[0][pz, py, px] >= thr)
            if int(l) == 1:
                n_pos += 1
                d = um_dist(pz - cz, py - cy, px - cx)
                if det and d <= mu:
                    n_hit += 1
                    errs.append(d)
            else:
                n_neg += 1
                n_det_neg += int(det)
    n_det = n_hit + n_det_neg
    return dict(recall=n_hit / max(n_pos, 1),
                mean_err_um=float(np.mean(errs)) if errs else float("nan"),
                neg_fpr=n_det_neg / max(n_neg, 1),
                count_ratio=n_det / max(n_pos, 1),  # proxy T_pred/T_true (want ~0.7-1)
                n_pos=n_pos, n_hit=n_hit, n_neg=n_neg)


def refresh_hard_negatives(model, ds, sampler, device):
    """Score train negatives, boost top-k peak responses (online HNM hook).

    Fixed (audit FLAG#1): scores sized to the FULL dataset and indexed by
    neg_id — the old neg-sized buffer overran past batch ~47. Fatal crash.
    """
    model.eval()
    scores = np.zeros(len(ds), dtype=np.float32)
    dl = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)
    with torch.no_grad():
        for k, (img, _, _) in enumerate(dl):
            prob = torch.sigmoid(model(img.to(device))).flatten(1).amax(1)
            v = prob.cpu().numpy()
            scores[k * 64:k * 64 + len(v)] = v
    neg_scores = scores[np.asarray(ds.neg_id)]
    hard = set(np.argsort(neg_scores)[-CONFIG["mine_topk"]:].tolist())
    w = np.where(ds.is_bright[ds.neg_id], CONFIG["bright_upsample"], 1.0)
    # hard holds POSITIONS within the neg array (not dataset ids)
    w[[i for i in range(len(ds.neg_id)) if i in hard]] *= CONFIG["mine_boost"]
    sampler.set_neg_weights(w)
    return len(hard)  # all top-k got boosted (bright 4x->16x, plain 1x->4x)


def train(args):
    set_seed(CONFIG["seed"] + args.seed_offset)
    print(f"torch {torch.__version__} cuda={torch.cuda.is_available()}", flush=True)
    use_cuda = torch.cuda.is_available() and not args.cpu
    if use_cuda:
        try:
            torch.zeros(1).cuda()
            name = torch.cuda.get_device_name(0)
            cap = torch.cuda.get_device_capability(0)
            print(f"gpu: {name} cap: {cap}", flush=True)
            if cap[0] < 7:
                # P100 sm_60 has no kernels in torch>=2.4 (3/3 lottery tickets).
                # CPU full training measured viable (~1.7 s/iter -> ~3.5 h/20ep).
                print(f"{name} unsupported by torch {torch.__version__}; "
                      f"CPU FULL training instead.", flush=True)
                use_cuda = False
        except Exception as e:
            print(f"CUDA unusable ({type(e).__name__}: {e}); CPU FULL training.", flush=True)
            use_cuda = False
    device = torch.device("cuda" if use_cuda else "cpu")
    if not use_cuda:
        # CPU full training is viable (measured ~1.7 s/iter VM-class ->
        # ~3.5 h for 20 epochs; Kaggle CPU similar). Checkpoints save per
        # improvement, so even a timeout leaves a usable model. (EXP-0035 log)
        print("CPU training full schedule "
              f"({args.epochs or CONFIG['epochs']} epochs)", flush=True)
    data_dir = args.data_dir or find_data_dir()
    print(f"data: {data_dir} device: {device}", flush=True)
    tr = PatchDataset(data_dir, CONFIG["train_split"])
    va = PatchDataset(data_dir, CONFIG["val_split"], tr.gmean, tr.gstd)
    print(f"train {CONFIG['train_split']}: N={len(tr)} pos={len(tr.pos_id)} "
          f"neg={len(tr.neg_id)} (bright={int(tr.is_bright[tr.neg_id].sum())}) "
          f"mean={tr.gmean:.1f} std={tr.gstd:.1f}", flush=True)
    print(f"val {CONFIG['val_split']}: N={len(va)} pos={len(va.pos_id)}", flush=True)
    bs = args.batch_size or CONFIG["batch_size"]
    sampler = BalancedBatches(tr, bs, CONFIG["pos_frac"], CONFIG["bright_upsample"],
                              CONFIG["seed"] + args.seed_offset, len(tr) // bs)
    tloader = DataLoader(tr, batch_sampler=sampler, num_workers=0)
    vloader = DataLoader(va, batch_size=64, shuffle=False, num_workers=0)
    model = UNet(CONFIG["base_ch"]).to(device)
    npar = sum(p.numel() for p in model.parameters())
    print(f"params: {npar / 1e6:.2f}M", flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=CONFIG["lr"],
                           weight_decay=CONFIG["weight_decay"])
    odir = out_dir()
    best, best_ep = -1.0, -1
    for ep in range(args.epochs if args.epochs is not None else CONFIG["epochs"]):
        model.train()
        tot, nb = 0.0, 0
        for img, tgt, _ in tloader:
            opt.zero_grad()
            out = torch.sigmoid(model(img.to(device)))
            tgt_d = tgt.to(device)
            # audit FLAG#6: design Opt-A loss = MSE + Dice-on-binarised-mask;
            # v9: foreground-weighted MSE (bg/fg ~230:1 locks all-zero otherwise)
            w = 1.0 + (CONFIG["fg_weight"] - 1.0) * (tgt_d > 0.5).float()
            loss = (((out - tgt_d) ** 2) * w).mean() \
                + dice_loss(out, (tgt_d > 0.5).float())
            loss.backward()
            opt.step()
            tot += loss.item()
            nb += 1
        m = validate(model, vloader, device)
        print(f"ep {ep}: loss={tot / max(nb, 1):.4f} val_recall={m['recall']:.3f} "
              f"err={m['mean_err_um']:.2f}um fpr={m['neg_fpr']:.3f} "
              f"cnt={m['count_ratio']:.2f}", flush=True)
        torch.save({"model": model.state_dict(), "cfg": CONFIG, "ep": ep},
                   odir / "unet_last.pt")
        # audit FLAG#3: select on recall SUBJECT to count discipline
        # (0.7<=cnt<=1.0 + documented FPR watch) — dense-output winners risk
        # the a=0.1 T_pred penalty (COMPETITION.md pitfall 3).
        gated = (0.7 <= m["count_ratio"] <= 1.0)
        if m["recall"] > best and gated:
            best, best_ep = m["recall"], ep
            torch.save({"model": model.state_dict(), "cfg": CONFIG, "ep": ep},
                       odir / "unet_best.pt")
        elif m["recall"] > best:
            print(f"  [gate] recall {m['recall']:.3f} best-so-far but cnt "
                  f"{m['count_ratio']:.2f} outside [0.7,1.0] — not saved as best",
                  flush=True)
        if CONFIG["mine_every"] and (ep + 1) % CONFIG["mine_every"] == 0 and not args.no_mine:
            nh = refresh_hard_negatives(model, tr, sampler, device)
            print(f"  [hnm] boosted {nh} hard negatives", flush=True)
    print(f"done. best_recall={best:.3f} @ep{best_ep} ckpts in {odir}", flush=True)


def smoke(args):
    """CPU smoke: synth fwd + 3 bwd steps, ckpt save/load, real-loader shapes."""
    set_seed(CONFIG["seed"])
    device = torch.device("cpu")
    model = UNet(CONFIG["base_ch"]).to(device)
    npar = sum(p.numel() for p in model.parameters())
    print(f"params: {npar} ({npar / 1e6:.2f}M)", flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    B = 4
    X = torch.randn(B, 1, *CONFIG["patch_shape"])
    T = torch.from_numpy(np.stack([gaussian_target()] * B)).unsqueeze(1)
    assert model(X).shape == (B, 1, *CONFIG["patch_shape"]), model(X).shape
    losses = []
    for _ in range(3):
        opt.zero_grad()
        l = nn.functional.mse_loss(torch.sigmoid(model(X)), T)
        l.backward()
        opt.step()
        losses.append(l.item())
    print(f"synth losses: {[round(v, 4) for v in losses]}", flush=True)
    assert losses[-1] < losses[0], "loss did not decrease"
    tmp = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "smoke_unet.pt"
    torch.save({"model": model.state_dict()}, tmp)
    m2 = UNet(CONFIG["base_ch"])
    m2.load_state_dict(torch.load(tmp, map_location="cpu", weights_only=True)["model"])
    s1 = sum(p.sum().item() for p in model.parameters())
    s2 = sum(p.sum().item() for p in m2.parameters())
    print(f"checkpoint OK: {tmp} (sums {s1:.4f}/{s2:.4f})", flush=True)
    assert abs(s1 - s2) < 1e-3
    # real loader path: first 8 manifest rows (shapes only, no training)
    data_dir = args.data_dir or find_data_dir()
    rows = list(csv.DictReader(open(f"{data_dir}/MANIFEST.csv")))[:8]
    print("first-8 manifest splits:", sorted({r['split'] for r in rows}), flush=True)
    for split in sorted({r["split"] for r in rows}):
        ds = PatchDataset(data_dir, split)
        for i in range(min(8, len(ds))):
            img, tgt, lab = ds[i]
            assert img.shape == (1, *CONFIG["patch_shape"]), img.shape
            assert tgt.shape == (1, *CONFIG["patch_shape"]), tgt.shape
    print("real-loader shape test OK (first-8-row splits)", flush=True)
    print("SMOKE PASS", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--no-mine", action="store_true")
    ap.add_argument("--cpu", action="store_true",
                    help="force CPU (diagnostic fallback)")
    a = ap.parse_args()
    smoke(a) if a.smoke else train(a)
