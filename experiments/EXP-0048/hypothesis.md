# EXP-0048 — EXP-0035 harvest readiness drill

## Hypothesis
EXP-0035 eval wiring (infer.py random-weights → BL.link → score) executes end-to-end
without weights, so unet_best.pt harvest converts to full eval in minutes.

## Background
UNet v9 RUNNING (CPU); logs silent while running. EXP-0035 run.sh waits on WEIGHTS_PATH.
HARVEST_RUNBOOK.md exists. This drill exercises the path with --random-weights.

## Falsification criteria
READY iff random-weight infer emits a node list + linking completes. Else BROKEN (fix before harvest).
