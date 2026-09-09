# EXP-0000 — plan (TEMPLATE, do not run)

- Data split: embryo-grouped CV per `docs/PROTOCOL.md` (never frame-random).
- Config/seeds: <config path + seed list>.
- Commands:
  ```bash
  python3 scripts/run_loop.py --exp EXP-0000 --dry-run
  ```
- Checks: trusted scorer runs; `metrics.json` written; RESULTS.md row appended.
