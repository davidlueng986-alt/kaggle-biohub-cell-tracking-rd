#!/usr/bin/env bash
# Runner for EXP-0049 — drift re-audit of submit_gold.ipynb (READ-ONLY audit).
# Runs static checks + behavioral probes vs repo sources of truth and writes
# experiments/EXP-0049/metrics.json. CPU-only, deterministic. Exit 0=IN-SYNC, 1=DRIFTED.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 experiments/EXP-0049/probe.py
