#!/usr/bin/env bash
# Scaffold a new experiment folder from template.
# Usage: ./scripts/new_experiment.sh EXP-XXXX "title"
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 EXP-XXXX \"title\"" >&2
  exit 1
fi

EXP_ID="$1"
shift
TITLE="$*"

if [[ ! "$EXP_ID" =~ ^EXP-[0-9]{4}$ ]]; then
  echo "error: EXP_ID must match EXP-XXXX (e.g. EXP-0001), got: $EXP_ID" >&2
  exit 1
fi

# Resolve repo root (parent of scripts/)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/experiments/$EXP_ID"

if [[ -e "$DIR" ]]; then
  echo "error: $DIR already exists" >&2
  exit 1
fi

mkdir -p "$DIR"

cat > "$DIR/hypothesis.md" <<EOF
# $EXP_ID — $TITLE

## Hypothesis
TODO: state falsifiable hypothesis.

## Background
TODO: link docs/PROTOCOL.md, knowledge/STATE.md entries.

## Falsification criteria
TODO: metric delta on frozen CV (embryo_id split: 6bba, 44b6) that would reject this.
EOF

cat > "$DIR/plan.md" <<EOF
# Plan — $EXP_ID $TITLE

## Config / seeds
TODO: seed(s), data split, embryo_id CV fold.

## Steps
1. TODO: code + config another agent can run cold.
2. Run \`./experiments/$EXP_ID/run.sh\` (or scripts/run_loop.sh).
3. Score with \`python3 scripts/score.py --pred <pred> --gt <gt>\`.

## Budget
12h T4 budget — TODO: record estimated runtime.
EOF

cat > "$DIR/metrics.json" <<EOF
{
  "exp_id": "$EXP_ID",
  "title": "$TITLE",
  "status": "planned",
  "score_simplified": null,
  "notes": "placeholder written by new_experiment.sh; overwrite with real scorer output"
}
EOF

cat > "$DIR/notes.md" <<EOF
# Notes — $EXP_ID $TITLE

## Log
- Created via scripts/new_experiment.sh.

## Decisions
TODO
EOF

cat > "$DIR/run.sh" <<EOF
#!/usr/bin/env bash
# Runner for $EXP_ID — $TITLE
# TODO: implement real train/infer/eval. Dry-run validates plumbing only.
set -euo pipefail
ROOT="\$(cd "\$(dirname "\$0")/../.." && pwd)"
echo "[$EXP_ID] dry-run: running SIMPLIFIED scorer..."
python3 "\$ROOT/scripts/score.py" --dry-run
echo "[$EXP_ID] TODO: replace with real pipeline; write metrics.json via score.py --out"
EOF
chmod +x "$DIR/run.sh"

echo "created $DIR/{hypothesis.md,plan.md,metrics.json,notes.md,run.sh}"
