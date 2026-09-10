#!/usr/bin/env bash
# Runner for EXP-0038 — T-discipline track filter (post-processing ONLY).
# Reuses frozen full-video pred graphs; no re-detection / re-linking.
# Steps: filter both samples -> score unfiltered + filtered with trusted
# scorer (true T_true from GT) -> assemble metrics.json + gate verdict.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0038"

echo "[EXP-0038] filtering frozen graphs..."
python3 "$EXP/filter_tracks.py" \
  --in "$ROOT/experiments/EXP-0009/full_6bba_05b6850b_pred.json" \
  --out "$EXP/filt_6bba_05b6850b_pred.json" \
  --stats-out "$EXP/filt_6bba_05b6850b_stats.json"
python3 "$EXP/filter_tracks.py" \
  --in "$ROOT/experiments/EXP-0021/6bba_05db0fb1_pred.json" \
  --out "$EXP/filt_6bba_05db0fb1_pred.json" \
  --stats-out "$EXP/filt_6bba_05db0fb1_stats.json"

echo "[EXP-0038] scoring (trusted scorer v1.1.0, true T_true)..."
python3 "$ROOT/scripts/score.py" \
  --pred "$ROOT/experiments/EXP-0009/full_6bba_05b6850b_pred.json" \
  --gt "$ROOT/experiments/EXP-0003/gt/6bba_05b6850b_gt.json" \
  --out "$EXP/score_unfilt_6bba_05b6850b.json" > /dev/null
python3 "$ROOT/scripts/score.py" \
  --pred "$EXP/filt_6bba_05b6850b_pred.json" \
  --gt "$ROOT/experiments/EXP-0003/gt/6bba_05b6850b_gt.json" \
  --out "$EXP/score_filt_6bba_05b6850b.json" > /dev/null
python3 "$ROOT/scripts/score.py" \
  --pred "$ROOT/experiments/EXP-0021/6bba_05db0fb1_pred.json" \
  --gt "$ROOT/experiments/EXP-0003/gt/6bba_05db0fb1_gt.json" \
  --out "$EXP/score_unfilt_6bba_05db0fb1.json" > /dev/null
python3 "$ROOT/scripts/score.py" \
  --pred "$EXP/filt_6bba_05db0fb1_pred.json" \
  --gt "$ROOT/experiments/EXP-0003/gt/6bba_05db0fb1_gt.json" \
  --out "$EXP/score_filt_6bba_05db0fb1.json" > /dev/null

echo "[EXP-0038] assembling metrics.json..."
python3 "$EXP/make_metrics.py"
echo "[EXP-0038] done."
