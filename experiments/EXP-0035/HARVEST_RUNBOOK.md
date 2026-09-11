# HARVEST RUNBOOK — EXP-0035 (weights → eval, zero-friction)

Training kernel: `liangwanyiudavid/biohub-unet-train-v1` (UNet v8, CPU FULL 20ep).
Eval: `experiments/EXP-0035/run.sh` (UNet heatmap → BL.link → score vs GT, window
6bba_05b6850b t20–29). Scorer: `scripts/score.py` v1.1.0. GT:
`experiments/EXP-0003/gt/6bba_05b6850b_gt.json`. DoG bar (same window, recomputed):
recall 0.893 / raw 0.7989 / adj 0.8194 (EXP-0009 ref @98.5).
Dry-validated 2026-09-11: run.sh empty WEIGHTS_PATH → exit 2 ✓;
`git check-ignore data/weights/x.pt` → ignored via `.gitignore:2:data/` ✓;
`kaggle kernels status|output|logs|files --help` + `kaggle competitions submissions --help` OK ✓.

All commands assume repo root `/home/box/workspace/kaggle-biohub-rd` and
`export PATH="$HOME/.local/bin:$PATH"`. Never print/commit secrets. No pushes/uploads/submits here.
Set `K=liangwanyiudavid/biohub-unet-train-v1` to save typing.

---

## (a) Check training status / logs (ONE snapshot max — do not poll in a loop)

```bash
export PATH="$HOME/.local/bin:$PATH"
K=liangwanyiudavid/biohub-unet-train-v1
kaggle kernels status $K            # want: KernelWorkerStatus.COMPLETE
kaggle kernels files $K             # confirm unet_best.pt (+ unet_last.pt) listed
```

If still RUNNING, read the tail once (no `-f` unless actively watching):

```bash
kaggle kernels logs $K 2>&1 | tail -30   # want: ep N/20, loss falling, val_recall, HNM lines
```

What good looks like: `val_recall > 0` by ~ep8–10, `best` checkpoint saved, HNM
`fired epN` lines (slice fix holds). See §(g) for kill/recalibrate triggers.

## (b) Fetch outputs + verify checkpoint

```bash
export PATH="$HOME/.local/bin:$PATH"
K=liangwanyiudavid/biohub-unet-train-v1
mkdir -p /tmp/unet-harvest
kaggle kernels output $K -p /tmp/unet-harvest
ls -la /tmp/unet-harvest   # want: unet_best.pt (+ unet_last.pt); note byte sizes
```

Verify the checkpoint (CPU-only, prints structural proof — keys/epoch/cfg):

```bash
python3 -c "
import torch
for f in ['unet_best.pt','unet_last.pt']:
    try:
        c = torch.load(f'/tmp/unet-harvest/{f}', map_location='cpu', weights_only=False)
    except FileNotFoundError:
        print(f, 'MISSING'); continue
    print(f, '| top-keys:', sorted(c.keys()), '| ep:', c.get('ep'), '| cfg:', c.get('cfg'))
    sd = c.get('model', {})
    print('   state_dict tensors:', len(sd), '| e0 weight:', tuple(sd['e0.n.0.weight'].shape) if 'e0.n.0.weight' in sd else 'KEY-MISSING')
"
```

Want: top-keys include `model` (+`cfg`, `ep`); e0 weight `(32,1,3,3,3)` (base-32 UNet
verbatim with `infer.py`). If `model` key missing → bad ckpt, STOP (do not edit
`infer.py`; report back — train-side re-export needed). If `cfg` missing, infer.py
falls back to train.py defaults (patch (16,48,48), thr 0.3) — usable but record it.

## (c) Place weights + set WEIGHTS_PATH (do NOT create data/weights/ early — only now)

```bash
git check-ignore data/weights/x.pt   # MUST print 'data/weights/x.pt' (ignored). If silent → STOP, report.
mkdir -p data/weights
cp /tmp/unet-harvest/unet_best.pt data/weights/unet_best.pt
ls -la data/weights/
```

Then set at the top of `experiments/EXP-0035/run.sh` (line 7):

```bash
WEIGHTS_PATH="$ROOT/data/weights/unet_best.pt"
```

(Use `$ROOT/...` absolute-via-ROOT form so run.sh works from any cwd. Prefer the
repo-relative copy over /tmp so the eval is reproducible. `data/` is gitignored —
weights never commit.)

## (d) Run EXP-0035 + read the verdict

Pre-flight (cheap, catches env/infra failures before the ~5 min infer):

```bash
python3 notebooks/train_unet/infer.py --self-test   # want: SELF-TEST PASS 5/5
```

Run:

```bash
time bash experiments/EXP-0035/run.sh   # expect ~5 min infer (10 fr × ~29 s) + <1 min link/score
```

Read the verdict:

```bash
cat experiments/EXP-0035/metrics.json
```

Verdict rule (frozen, `hypothesis.md`): SIGNAL iff learned window recall **>**
DoG window recall **AND** learned window edge_raw **≥** DoG window edge_raw
**AND** det/frame ≤ 2× GT/frame — else REJECT. Compare against the recomputed
same-window DoG numbers printed in `metrics.json` (`dog_window_bar`), never pasted bars.
Sanity: `linked: N nodes -> M edges`, `det_per_frame` vs `gt_per_frame`.

Failure modes + fixes (trace of `run.sh` + `infer.py`):
| Symptom | Meaning | Fix |
|---|---|---|
| `weights not landed ...` exit 2 | WEIGHTS_PATH empty or file missing | §(c) again; check path spelling |
| `KeyError: 'model'` / `Missing key(s) in state_dict` / size mismatch | ckpt keys/arch ≠ train.py UNet | STOP, report (train-side re-export; never patch infer.py arch ad-hoc) |
| `FileNotFoundError: data/patches/MANIFEST.csv` (norm step) | local patches absent | pass `--mean 532.89 --std 581.22` via infer.py directly, or restore `data/patches/` |
| OOM / process killed mid-frame | `--batch 8` too big for RAM | rerun infer with `--batch 2` (slower, same math) |
| ≫10 min / hung frame | pathological tiling or thrash | check per-frame `t=.. heat_max=.. n_det=..` lines; `n_det` in tens of thousands+ = thr/noise issue, see §(g) |
| `n_det = 0` every frame | dead model (all-negative heat) | threshold/loss review per §(g); record honestly, do not lower thr to shop a SIGNAL |

## (e) Record results (STATE / RESULTS / HYPOTHESES + commit template)

Update exactly these three lines (keep table/Next-line conventions):
1. `knowledge/RESULTS.md` line 63 (`| EXP-0035 | ... | learned-detector eval (planned) |`):
   replace `— (awaits unet_best.pt)` with learned vs DoG numbers
   (recall, raw, adj, det/frame) and SIGNAL/REJECT.
2. `knowledge/HYPOTHESES.md`: append dated Next-line under the GPU/UNet thread
   (mirror existing `- 2026-09-11 (STAGE A): ...` style, ending `Next: ...`).
3. `knowledge/STATE.md`: update the `experiments/EXP-0035/` skeleton bullet (§What
   exists) + the `UNet v8:` bullet + the `Next:` line — verdict + numbers, no
   fabricated digits; `metrics.json` is the source of truth.

Commit message template (repo convention `EXP-00NN H-00X ... -> decision: ...`):

```bash
git add experiments/EXP-0035/ knowledge/RESULTS.md knowledge/HYPOTHESES.md knowledge/STATE.md
git commit -m "EXP-0035 H-002/GPU learned-detector t20-29: recall X.XXX vs DoG 0.893, raw X.XXXX -> decision: SIGNAL|REJECT (+ next step)"
```

(Never `git add data/weights/` — gitignored; verify with `git status --short`.)

## (f) Timeout-harvest path (best never saved — use unet_last.pt, label honestly)

Trigger: kernel COMPLETE/TIMEOUT with no `unet_best.pt` (e.g. count-gate withheld
best the whole run — val_recall stuck 0) but `unet_last.pt` exists.

```bash
cp /tmp/unet-harvest/unet_last.pt data/weights/unet_last.pt
# in run.sh: WEIGHTS_PATH="$ROOT/data/weights/unet_last.pt"
time bash experiments/EXP-0035/run.sh
```

Label honestly everywhere (non-gated — this number does NOT clear the gate):
- `metrics.json notes`: append `weights=unet_last.pt (TIMEOUT harvest, non-gated last-epoch — NOT recall-gated best)`.
- RESULTS.md EXP-0035 row: prefix numbers with `last-ep (non-gated):`.
- Commit: `EXP-0035 H-002/GPU timeout-harvest unet_last.pt (non-gated): recall ... -> decision: REPLAN|REJECT (no gate impact)`.
- Verdict still computed by the same rule, but a SIGNAL on last-epoch weights is
  provisional — replication on gated `unet_best.pt` (or retrain) required before any
  promotion claim. Do NOT edit hypothesis.md falsification criteria to fit.

## (g) Kill / recalibrate triggers (read from `kaggle kernels logs $K`)

- **Recall 0 past ep8–10** (val_recall/cnt still 0): zero-positive regime persisting
  past warmup → threshold/loss review (peak_thr 0.3 too high? MSE-only drift? count-gate
  masking?). Do not harvest-yet-eval early; let it run to ep12, then decide.
- **Loss flat** (e.g. 0.5318→0.5018 then no movement ≥3 eps): optimizer stuck or
  loss insensitive (Dice term missing?) → flag for train-owner; keep run going (cheap)
  but start replan note.
- **HNM crash signatures**: `IndexError`/slice traceback at ep-N refresh, or
  `boost` position/index confusion (HNM fired line followed by NaN loss / explosion
  in `n_det`) → the v8 slice fix regressed; kill, report traceback, do not eval partial ckpts.
- **Count explosion in eval** (`det_per_frame` > 2× GT, tens of thousands of dets like the
  random-weight dry run's 17209): model uncalibrated → REJECT per rule, recalibrate thr
  as a NEW hypothesis (never re-run same EXP-0035 window with tuned thr and call it SIGNAL).
- **Kernel TIMEOUT before ep20**: go to §(f); record `~1.25 h/epoch` timing vs 12 h cap.
