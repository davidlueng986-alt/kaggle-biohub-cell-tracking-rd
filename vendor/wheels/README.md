# Vendored wheels for the Kaggle offline submit path (GOLD §5)

The `*.whl` files in this directory are git-ignored (binaries, ~10 MB);
their canonical store is the Kaggle dataset
`liangwanyiudavid/biohub-zarr-wheels` (attached to the submit kernel via
`dataset_sources`, installed offline with `pip --no-index --find-links`).

Re-download recipe (cp312-manylinux, matching the Kaggle image):

```bash
python3 - <<'EOF'
import json, urllib.request, os
os.makedirs("vendor/wheels", exist_ok=True)
def pick(pkg, pred):
    d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json"))
    c = [f for f in d["urls"] if f["filename"].endswith(".whl") and pred(f["filename"])]
    return sorted(c, key=lambda f: f["filename"])[-1]
def x86(fn): return "cp312" in fn and "x86_64" in fn
def anypy(fn): return fn.endswith("py3-none-any.whl")
for pkg, pred in [("zarr", lambda fn: x86(fn) or anypy(fn)), ("numcodecs", x86),
                  ("google-crc32c", x86), ("donfig", anypy), ("packaging", anypy),
                  ("typing_extensions", anypy)]:
    f = pick(pkg, pred)
    urllib.request.urlretrieve(f["url"], os.path.join("vendor/wheels", f["filename"]))
    print("got", f["filename"])
EOF
```

Then `kaggle datasets create -p vendor/wheels` (after `datasets init` +
editing `dataset-metadata.json`), or `kaggle datasets version -p ...` to
refresh the existing dataset.
