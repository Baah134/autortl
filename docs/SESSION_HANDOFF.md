# AutoRTL current checkpoint

One current section only. History lives in `docs/PROGRESS.md` and Git. The plan
of record is `docs/ROADMAP.md`; the review behind it is
`docs/REVIEW_2026-11-15.md`.

## Current — November 15, 2026: final comparison running

Coordinator: Claude. Branch `codex/contract-context`, pushed to `origin` on
November 15 (MIT licence added). `main` frozen at `ca61dbc`; no PR yet.

**Running:** `final-01`, the registered comparison (40 tasks x 3 arms x 3
trials = 360 cells, runtime `775820583`), launched November 15 08:47 from
`C:/Users/prince.baah/autortl-private/final-01` with `run_all.sh`. Log:
`final-01/run_all.log`. It stops by itself on a model block (quota) or three
consecutive interrupted cells, and can be restarted with the same command;
cells are never rerun. Expected about 19 hours of awake machine time.

**Do not edit while it runs:** `autortl/`, `llm/`, `data/`, `.claude/skills/`,
`run.py`, `benchmark/pilot.py`, `benchmark/verilogeval.py` (each cell records
the runtime it launched). Use a worktree for code changes.

**Exact next action:** ROADMAP task B1. When the log ends with `all cells
attempted`, grade with `python -m benchmark.report grade`, render the report,
archive it under `evidence/<date>/final-01-results/`, then B2 (decide the
claim) and P3 (README numbers). If the log shows `=== STOPPED`, follow B1's
restart notes.

**State of the work**
- Pilot gate passed (pilot-06: single call, ablation and full each 6/6);
  final registration frozen (`evidence/2026-11-14/final-registration-01`).
- Benchmark code complete and tested: `benchmark/{verilogeval,pilot,
  registration,campaign,report}.py`; runbook `docs/BENCHMARK_PILOT.md`.
- Harness fixes from the pilots are merged with tests and live checks:
  clockless and single-register timing, resetless modules, arm B policy seam,
  missing-tool and crash triage. Full suites were green at 2,287 harness and
  323 tooling tests before the November 15 additions (benchmark report,
  campaign and lease-keeper tests, all passing).
- Open research risk: `planner_spec_error_shared_by_oracle_and_rtl` (ROADMAP V1).
- Parked, untouched: Codex's November 13 candidate-export stage in
  `C:/Users/prince.baah/Documents/Codex/2026-10-15/hey/work/nov13-candidate-bundle-stage`
  (needed only for latest-complete selection and parallel campaigns).

**Owner decisions pending:** PR and merge to `main`, benchmark B3
task source, pinned model name, board authorisation (ROADMAP section 7).

**Environment:** see ROADMAP section 3. Keep the machine awake; renew the
lease with `python scripts/lease_keeper.py --token-file <private file>`.
