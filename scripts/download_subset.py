#!/usr/bin/env python3
"""Subset downloader (AUDIT-FIX I1/I7).

Auth (no secrets in repo): Kaggle CLI resolves credentials itself from EITHER
  - env: KAGGLE_USERNAME + KAGGLE_KEY, OR
  - file: ~/.kaggle/kaggle.json (chmod 600).
This script preflights that BEFORE paginating so a missing auth fails fast with
an actionable message instead of a cryptic list_error. KGAT Bearer-only setups
(~/.kaggle/access_token without kaggle.json/env) must run `kaggle auth login`
or export the env pair first. Requires kaggle CLI >= 2.2 for `--format csv`
(verified: 2.2.4). Competition Rules must be accepted on the web page first
(API returns 403 until accepted). Never commit kaggle.json / .env / tokens.
See docs/AUTH.md.
"""
import os
import subprocess, pathlib, sys, time

# AUDIT-FIX I1: repo-relative root (was absolute checkout hardcode), override
# via BIOHUB_DATA_DIR. Resolves to the same path on the canonical VM.
REPO = pathlib.Path(__file__).resolve().parent.parent
root = pathlib.Path(os.environ.get("BIOHUB_DATA_DIR", REPO / "data"))


def check_auth():
    """Fail fast with guidance if the Kaggle CLI has no usable credentials."""
    env_ok = bool(os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"))
    kj = pathlib.Path.home() / ".kaggle" / "kaggle.json"
    file_ok = kj.exists() and kj.stat().st_size > 0
    if env_ok or file_ok:
        print(f"auth OK (env={'yes' if env_ok else 'no'}, kaggle.json={'yes' if file_ok else 'no'})",
              flush=True)
        return
    print("AUTH MISSING: Kaggle CLI has neither KAGGLE_USERNAME/KAGGLE_KEY env "
          "nor ~/.kaggle/kaggle.json.", flush=True)
    print("Fix (pick one, secrets stay out of the repo):", flush=True)
    print("  kaggle auth login   # interactive, stores under ~/.kaggle/", flush=True)
    print("  # or: Kaggle Settings -> API -> Create New Token -> ~/.kaggle/kaggle.json (chmod 600)", flush=True)
    print("  # or: export KAGGLE_USERNAME=... KAGGLE_KEY=...  (see docs/AUTH.md)", flush=True)
    print("Then accept competition Rules on the web page and re-run.", flush=True)
    sys.exit(3)


check_auth()
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
