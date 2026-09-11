#!/usr/bin/env python3
"""EXP-0059 step 2: fresh-detect assigned-but-missing (sample,pct) combos.

Cap rationale (recorded BEFORE any linking/scoring, 2026-09-11):
frozen rule needs 4 missing combos x 100f = 400 > 300 cap. Omit
44b6_0113de3b@96 (bright reference tissue, recall-saturated at @99; cannot
decide the worst-bar verdict, already pinned sub-BTE by frozen 0b24845f@99).
Fresh (exactly 300f): 6bba_05b6850b@96, 6bba_062c8d37@96, 6bba_05db0fb1@99.
Uses scripts/dog_detect.py main() in-process (exact CLI code path/defaults).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/box/workspace/kaggle-biohub-rd/scripts")
from dog_detect import main as dog_main  # noqa: E402

DATA = "/home/box/workspace/kaggle-biohub-rd/data/train"
DET = os.path.join(HERE, "det")
COMBOS = [("6bba_05b6850b", 96.0), ("6bba_062c8d37", 96.0), ("6bba_05db0fb1", 99.0)]
FRAMES = list(range(100))


def main():
    os.makedirs(DET, exist_ok=True)
    n_new = 0
    for sid, pct in COMBOS:
        for t in FRAMES:
            out = os.path.join(DET, f"{sid}_p{pct}_t{t}.json")
            if os.path.exists(out):
                continue
            rc = dog_main([os.path.join(DATA, f"{sid}.zarr"), "--t", str(t),
                           "--pct", str(pct), "--out", out])
            assert rc == 0, (sid, pct, t)
            n_new += 1
    print(f"fresh frames written this run: {n_new} (cap 300; combos={COMBOS})")
    assert n_new <= 300


if __name__ == "__main__":
    main()
