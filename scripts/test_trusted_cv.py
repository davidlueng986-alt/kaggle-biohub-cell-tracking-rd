#!/usr/bin/env python3
"""Unit tests for trusted_cv harness (stdlib unittest, no data needed).

Run: python3 scripts/test_trusted_cv.py -v
Covers: fit_best argmax + deterministic tie-breaks (micro desc, fewer
detections, smaller gate, higher pct). No zarr/data/GPU required.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from trusted_cv import fit_best


def row(edge, n_det):
    return {"edge": edge, "raw": edge, "div": 0.0, "score": edge,
            "ec": {"TP": 10, "FP": 1, "FN": 1}, "dc": {"TP": 0, "FP": 0, "FN": 0},
            "n_det": n_det, "assign": "pure", "T_true": 1000}


class TestFitBest(unittest.TestCase):
    def test_argmax(self):
        cache = {("s", 98.5, 7.0): row(0.5, 100),
                 ("s", 99.0, 7.0): row(0.7, 100)}
        (bp, bg), _ = fit_best(["s"], [(98.5, 7.0), (99.0, 7.0)], cache, None)
        self.assertEqual((bp, bg), (99.0, 7.0))

    def test_tie_fewer_detections(self):
        cache = {("s", 98.5, 7.0): row(0.5, 200),
                 ("s", 99.0, 7.0): row(0.5, 100)}
        (bp, bg), _ = fit_best(["s"], [(98.5, 7.0), (99.0, 7.0)], cache, None)
        self.assertEqual((bp, bg), (99.0, 7.0))  # same micro, fewer dets wins

    def test_tie_smaller_gate_then_higher_pct(self):
        cache = {("s", 98.5, 7.0): row(0.5, 100),
                 ("s", 98.5, 10.0): row(0.5, 100),
                 ("s", 99.0, 10.0): row(0.5, 100)}
        (bp, bg), _ = fit_best(["s"], [(98.5, 7.0), (98.5, 10.0), (99.0, 10.0)],
                               cache, None)
        self.assertEqual((bp, bg), (98.5, 7.0))

    def test_deterministic(self):
        cache = {("a", 98.0, 7.0): row(0.6, 150),
                 ("b", 98.0, 7.0): row(0.4, 150),
                 ("a", 99.0, 7.0): row(0.6, 150),
                 ("b", 99.0, 7.0): row(0.4, 150)}
        r1, _ = fit_best(["a", "b"], [(98.0, 7.0), (99.0, 7.0)], cache, None)
        r2, _ = fit_best(["b", "a"], [(99.0, 7.0), (98.0, 7.0)], cache, None)
        self.assertEqual(r1, r2)  # order-invariant


if __name__ == "__main__":
    unittest.main()
