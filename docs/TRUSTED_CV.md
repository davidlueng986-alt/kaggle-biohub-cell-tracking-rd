# Trusted CV v1.2 — operational brief (PM)

Normative: `docs/PROTOCOL.md` v1.2. Scorer unchanged (`scripts/score.py` v1.1.0).

## Goal
Rebuild Grandmaster-style nested CV so standing numbers are honest. Do **not** trust:
- Historical image **0.8194** (`tuned_ref` — HPs locked on scored samples)
- External public LB **Forge 0.946** (`lb_external_untrusted` — may be public-overfit)

**BTE** = beat our best `trusted` `loso_worst` (then `loso_micro`).

## Subset (current)
```
44b6_0113de3b  44b6_0b24845f  44b6_0c582fdc
6bba_05b6850b  6bba_05db0fb1  6bba_062c8d37
```

## Implement now
1. `scripts/trusted_cv.py` — LOSO + embryo-nested runners; JSON envelope with `cv_tag`, `loso_*`, `embryo_nested_worst`, per-left-out HP provenance.
2. Default HP grid for standing DoG rebaseline: percentiles `{96.0,97.0,98.0,98.5,99.0,99.5}` × gate `{7,10}` (link-only; no forks unless declared). Fit = argmax trusted score on the **fit** samples only (micro), then score held-out.
3. New experiment (next free id, e.g. EXP-0053): rebaseline current DoG+link stack under trusted CV → new standing. Retag EXP-0010 0.8194 as `tuned_ref` in RESULTS.
4. `knowledge/LB_CALIBRATION.md` — table of our (trusted, public_lb) pairs; separate untrusted external row for Forge.
5. Update STATE.md protocol pointer to v1.2; standing section uses only `trusted` numbers.
6. Unit smoke: dry-run on 2 samples must finish; full 6-sample LOSO may be long — run full for standing rebaseline.

## Out of scope
- Do not chase Forge 0.946 as a numeric target.
- Do not promote on public LB alone.
- Do not invent product direction beyond this brief + PROTOCOL v1.2.
