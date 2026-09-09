#!/usr/bin/env python3
import subprocess, pathlib, sys, time
root = pathlib.Path("/home/box/workspace/kaggle-biohub-rd/data")
ids = [l.strip() for l in (root / "SUBSET_IDS.txt").read_text().splitlines() if l.strip()]
print("target ids", ids, flush=True)
token = None
matched = []
stale = 0
while True:
    cmd = [
        "kaggle", "competitions", "files",
        "-c", "biohub-cell-tracking-during-development",
        "--page-size", "200", "--format", "csv",
    ]
    if token:
        cmd += ["--page-token", token]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("list_error", e.returncode, (e.output or "")[:300], flush=True)
        break
    next_tok = None
    before = len(matched)
    for line in out.splitlines():
        if line.startswith("Next Page Token"):
            next_tok = line.split("=", 1)[-1].strip()
            continue
        if not line or line.startswith("name"):
            continue
        name = line.split(",")[0]
        for sid in ids:
            if (
                name.startswith(f"train/{sid}.geff/")
                or name.startswith(f"train/{sid}.zarr/")
                or name.startswith(f"train/{sid}/")
            ):
                matched.append(name)
                break
    gained = len(matched) - before
    found_ids = {sid for sid in ids if any(
        n.startswith(f"train/{sid}.geff/")
        or n.startswith(f"train/{sid}.zarr/")
        or n.startswith(f"train/{sid}/")
        for n in matched
    )}
    missing = [sid for sid in ids if sid not in found_ids]
    print(
        f"scan matched={len(matched)} gained={gained} found_ids={len(found_ids)}/{len(ids)} "
        f"missing={missing[:3]}{'...' if len(missing)>3 else ''} next={bool(next_tok)}",
        flush=True,
    )
    if gained == 0:
        stale += 1
    else:
        stale = 0
    # stop only when every target id has files, or listing ends
    if not next_tok:
        break
    if not missing and stale >= 1:
        break
    # never early-stop while ids still missing (old stale>=3 skipped 6bba)
    token = next_tok

matched = sorted(set(matched))
(root / "SUBSET_FILES.txt").write_text("\n".join(matched) + "\n")
print("unique matched", len(matched), flush=True)
if not matched:
    sys.exit(2)
ok = fail = 0
for i, name in enumerate(matched):
    dest_dir = root / pathlib.Path(name).parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    basename = pathlib.Path(name).name
    if (dest_dir / basename).exists() and (dest_dir / basename).stat().st_size > 0:
        ok += 1
        continue
    for attempt in range(3):
        try:
            subprocess.check_call(
                [
                    "kaggle", "competitions", "download",
                    "-c", "biohub-cell-tracking-during-development",
                    "-f", name,
                    "-p", str(dest_dir),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            ok += 1
            break
        except Exception as e:
            if attempt == 2:
                fail += 1
                print("FAIL", name, e, flush=True)
            else:
                time.sleep(2)
    if (i + 1) % 25 == 0:
        print(f"progress {i+1}/{len(matched)} ok={ok} fail={fail}", flush=True)
print("DONE ok", ok, "fail", fail, flush=True)
