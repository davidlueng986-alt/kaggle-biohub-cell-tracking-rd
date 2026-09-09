#!/usr/bin/env bash
# Runner for EXP-0001 — Embryo-CV baseline harness (H-001).
# Dry-run only: validates scorer + loop plumbing with toy pred/gt JSON.
# Stdlib only, no data download, no GPU. Exits 0 on success.
set -euo pipefail

EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$EXP_DIR/../.." && pwd)"

echo "[EXP-0001] step 1/3: SIMPLIFIED scorer --dry-run (plumbing check)..."
python3 "$ROOT/scripts/score.py" --dry-run

echo "[EXP-0001] step 2/3: writing toy pred/gt JSON (embryo-CV stand-ins, no real data)..."
# fold0 = holdout 44b6 stand-in (promotion fold per PROTOCOL v1.0 §2)
cat > "$EXP_DIR/fold0_pred.json" <<'EOF'
{"edges": [[1, 2], [2, 3], [3, 4]], "divisions": [[1, 2, 3]]}
EOF
cat > "$EXP_DIR/fold0_gt.json" <<'EOF'
{"edges": [[1, 2], [2, 3], [4, 5]], "divisions": [[1, 2, 3]]}
EOF
# fold1 = holdout 6bba stand-in (stability check; deliberate division miss)
cat > "$EXP_DIR/fold1_pred.json" <<'EOF'
{"edges": [[10, 11], [11, 12]], "divisions": [[10, 20, 21]]}
EOF
cat > "$EXP_DIR/fold1_gt.json" <<'EOF'
{"edges": [[10, 11], [11, 13]], "divisions": [[10, 20, 22]]}
EOF

echo "[EXP-0001] step 3/3: scoring toy folds via scripts/score.py --pred --gt --out ..."
python3 "$ROOT/scripts/score.py" --pred "$EXP_DIR/fold0_pred.json" --gt "$EXP_DIR/fold0_gt.json" --out "$EXP_DIR/fold0_scores.json"
python3 "$ROOT/scripts/score.py" --pred "$EXP_DIR/fold1_pred.json" --gt "$EXP_DIR/fold1_gt.json" --out "$EXP_DIR/fold1_scores.json"

python3 - "$EXP_DIR" <<'EOF'
import json, sys
exp_dir = sys.argv[1]
fold0 = json.load(open(f"{exp_dir}/fold0_scores.json"))
fold1 = json.load(open(f"{exp_dir}/fold1_scores.json"))
metrics = {
    "exp_id": "EXP-0001",
    "title": "Embryo-CV baseline harness",
    "hypothesis_id": "H-001",
    "protocol_version": "1.0",
    "dry_run": True,
    "simplified_scorer": True,
    "scores": {
        "fold0_holdout_44b6_toy": fold0,
        "fold1_holdout_6bba_toy": fold1,
    },
    "expected_hand_calc": {
        "fold0_edge_jaccard": 0.5,
        "fold0_division_jaccard": 1.0,
        "fold0_score": 0.6,
    },
    "hand_calc_match_fold0": (
        abs(fold0["adjusted_edge_jaccard_simplified"] - 0.5) < 1e-9
        and abs(fold0["division_jaccard_simplified"] - 1.0) < 1e-9
        and abs(fold0["score_simplified"] - 0.6) < 1e-9
    ),
    "decision": "keep-trying",
    "decision_reason": (
        "Dry-run harness only (no real data, SIMPLIFIED scorer). "
        "H-001 transfer claim untested; needs Kaggle auth + data + full geff scorer. "
        "Next: EXP-0002 real embryo-CV baseline once unblocked."
    ),
}
assert metrics["hand_calc_match_fold0"], "fold0 scorer output disagrees with hand calc — scorer bug, see PROTOCOL §1"
json.dump(metrics, open(f"{exp_dir}/metrics.json", "w"), indent=2)
print(json.dumps(metrics, indent=2))
EOF

echo "[EXP-0001] OK: metrics.json written from real scorer output."
