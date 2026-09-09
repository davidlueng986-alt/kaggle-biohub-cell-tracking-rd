#!/usr/bin/env python3
import subprocess, pathlib, sys
root = pathlib.Path("/home/box/workspace/kaggle-biohub-rd/data")
ids_path = root / "SUBSET_IDS.txt"
if not ids_path.exists():
    print("missing SUBSET_IDS.txt", file=sys.stderr); sys.exit(1)
ids = [l.strip() for l in ids_path.read_text().splitlines() if l.strip()]
print("target ids", ids)
token = None
matched = []
while True:
    cmd = [
        "kaggle", "competitions", "files",
        "-c", "biohub-cell-tracking-during-development",
        "--page-size", "200", "--format", "csv",
    ]
    if token:
        cmd += ["--page-token", token]
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    next_tok = None
    for line in out.splitlines():
        if line.startswith("Next Page Token"):
            next_tok = line.split("=", 1)[-1].strip()
            continue
        if not line or line.startswith("name"):
            continue
        name = line.split(",")[0]
        for sid in ids:
            if name.startswith(f"train/{sid}.") or f"/{sid}." in name[:80]:
                matched.append(name)
                break
    token = next_tok
    print(f"scan matched={len(matched)} next={bool(next_tok)}")
    if not next_tok:
        break
# dedupe
matched = sorted(set(matched))
(root / "SUBSET_FILES.txt").write_text("\n".join(matched) + "\n")
print("unique matched", len(matched))
ok = fail = 0
for i, name in enumerate(matched):
    dest = root / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    # kaggle -p puts file in dir with basename sometimes
    basename = pathlib.Path(name).name
    candidates = [dest, dest.parent / basename]
    if any(p.exists() and p.stat().st_size > 0 for p in candidates):
        ok += 1
        continue
    try:
        subprocess.check_call(
            [
                "kaggle", "competitions", "download",
                "-c", "biohub-cell-tracking-during-development",
                "-f", name,
                "-p", str(dest.parent),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        ok += 1
    except Exception as e:
        fail += 1
        print("FAIL", name, e)
    if (i + 1) % 25 == 0:
        print(f"progress {i+1}/{len(matched)} ok={ok} fail={fail}")
print("DONE ok", ok, "fail", fail)
