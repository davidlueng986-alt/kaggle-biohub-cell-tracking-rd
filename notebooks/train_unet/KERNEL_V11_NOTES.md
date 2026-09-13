# UNet v11 Kaggle-kernel spec (COUNT DISCIPLINE + calibration — NOT recall)

PM green-light: attack count discipline + calibration/threshold. Do NOT chase recall.

## What v11 changes (vs v10, in `train.py` only)

- `CONFIG`: `fpr_max=0.10`, `cnt_lo/cnt_hi=[0.7,1.0]`, `det_max=3.0` det/patch,
  `fp_penalty=1.0` (single train-side calibration knob: extra E[prob^2] on NEG
  patches; doubles background suppression, penalises FP floods).
- `validate()`: adds density proxies — `det_per_patch` (local-max peak count
  via `max_pool3d (3,9,9)`, mirrors `infer.py:extract_peaks`, no NMS so it is a
  conservative upper bound) + `neg_over_thr` (neg supra-threshold voxel frac).
- `gate_decision()`: best requires recall AND count/FPR AND density together.
  Hard REJECT (explicit `[gate] REJECT` log, never saved) on: recall not above
  best, `n_hit==0` (cnt==1.0 built purely from FPs), `fpr > fpr_max` (fpr~1
  floods), cnt outside window, density above `det_max`.
- Per-epoch log now prints `recall + cnt + fpr + dens/patch + negovr` every epoch.
- `python3 train.py --smoke` runs `gate_self_test()`: synthetic 26k-det flood
  REJECTED, cnt==1.0/recall-0 degenerate REJECTED, sane ACCEPTED, uniform-flood
  density (36864 peaks/patch) trips the density proxy.

## Prior fixes kept intact (do NOT regress)

HNM slice-overrun fix, recall-only selection replaced by gate, fg-weighted MSE
(Dice OFF), cuda seed/sampler determinism, peak_thr=0.1.

## New kernel (NEVER reuse v1 — `biohub-unet-train-v1` is CANCEL_ACKNOWLEDGED)

New slug: `liangwanyiudavid/biohub-unet-train-v11`

Push from a LATER stage with network + kaggle credentials (no kaggle calls were
made by the TRAIN subagent). Exact one-step sequence:

```bash
cd /home/box/workspace/kaggle-biohub-rd
rm -rf /tmp/v11kernel && mkdir -p /tmp/v11kernel
cp notebooks/train_unet/train.py /tmp/v11kernel/
cat > /tmp/v11kernel/kernel-metadata.json <<'EOF'
{"code_file": "train.py", "competition_sources": ["biohub-cell-tracking-during-development"], "dataset_sources": ["liangwanyiudavid/biohub-train-patches"], "enable_gpu": true, "enable_internet": false, "id": "liangwanyiudavid/biohub-unet-train-v11", "is_private": true, "kernel_type": "script", "language": "python", "title": "biohub-unet-train-v11"}
EOF
kaggle kernels push -p /tmp/v11kernel
```

GPU run command inside the kernel (full schedule, gated past ep4):

```bash
python3 train.py --epochs 20 --batch-size 16
```

Expected: ~20 gated epochs; `unet_best.pt` only on ACCEPT
(recall-up + cnt in [0.7,1.0] + fpr<=0.10 + dens<=3.0/patch);
`unet_last.pt` every epoch (timeout-safe). CPU fallback is automatic
(P100 sm_60 / no-GPU → full CPU schedule).

## Watch signals (first GPU run)

- ep0: expect possible REJECT (random-init flood: recall~0/cnt~1.0/fpr~1,
  dens>>3) — healthy gate fire, NOT a failure.
- Escape signal: loss falling + recall>0 with dens/patch < 3 and fpr < 0.10.
- Red flag: dens/patch climbing into hundreds while cnt stays in window
  (patch-argmax blindness) — density gate must REJECT; if ACCEPTs, lower
  `det_max` before any further push.
