#!/usr/bin/env python3
"""EXP-0060 step 2: fresh-detect assigned-but-missing (sample,pct) combos.

Sign-corrected LOSO+nested needs 7 combos; 5 reuse frozen artifacts:
  0113de3b@99 (EXP-0008), 0b24845f@96 (EXP-0040), 0c582fdc@96 (EXP-0040),
  05b6850b@99 (EXP-0008), 05db0fb1@96 (EXP-0039).
Missing (fresh, exactly 200f = at the 200f cap):
  6bba_062c8d37@99 (LOSO + nested fit-44b6 arm) and 44b6_0113de3b@96
  (nested fit-6bba arm assigns all three 44b6 samples @96 since every 44b6
  B exceeds the 6bba fit-median 85.89; 0113de3b@96 was never detected).
Uses scripts/dog_detect.py main() in-process (exact CLI code path/defaults).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/box/workspace/kaggle-biohub-rd/scripts")
from dog_detect import main as dog_main  # noqa: E402

DATA = "/home/box/workspace/kaggle-biohub-rd/data/train"
DET = os.path.join(HERE, "det")
COMBOS = [("6bba_062c8d37", 99.0), ("44b6_0113de3b", 96.0)]
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
    print(f"fresh frames written this run: {n_new} (cap 200; combos={COMBOS})")
    assert n_new <= 200


if __name__ == "__main__":
    main()
