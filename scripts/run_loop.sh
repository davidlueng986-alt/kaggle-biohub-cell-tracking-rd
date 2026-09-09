#!/usr/bin/env bash
# Loop runner smoke check.
# Usage: ./scripts/run_loop.sh [--dry-run]
# --dry-run: checks structure, runs scorer dry-run, validates EXP folders have metrics.json; exits 0.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

fail() { echo "run_loop: FAIL: $*" >&2; exit 1; }

echo "run_loop: root=$ROOT dry_run=$DRY_RUN"

# 1. Required shared files exist
for f in scripts/score.py scripts/new_experiment.sh scripts/run_loop.sh; do
  [[ -f "$ROOT/$f" ]] || fail "missing required file $f"
  echo "run_loop: found $f"
done

# 2. Scorer dry-run must succeed
python3 "$ROOT/scripts/score.py" --dry-run > /tmp/run_loop_scorer.json
echo "run_loop: scorer --dry-run OK"

# 3. Validate experiments/ folders (if any): each EXP-*/ must have metrics.json
if [[ -d "$ROOT/experiments" ]]; then
  for d in "$ROOT"/experiments/EXP-*/; do
    [[ -d "$d" ]] || continue
    [[ -f "$d/metrics.json" ]] || fail "experiment $d missing metrics.json"
    python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$d/metrics.json" \
      || fail "experiment $d/metrics.json is not valid JSON"
    echo "run_loop: validated $d/metrics.json"
  done
else
  echo "run_loop: no experiments/ dir yet (ok for scaffold stage)"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "run_loop: --dry-run OK (structure + scorer + EXP metrics.json validation)"
  exit 0
fi

# Full (non-dry) loop is a Stage-3 concern; keep exit 0 with guidance for now.
echo "run_loop: full loop not implemented in scaffold stage (Stage3 EXP-0001 owns it). Exiting 0."
exit 0
