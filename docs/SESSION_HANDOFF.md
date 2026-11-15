# AutoRTL current checkpoint

One current section only. History lives in `docs/PROGRESS.md` and Git. The plan
of record is `docs/ROADMAP.md`; the review behind it is
`docs/REVIEW_2026-11-15.md`.

## Current — November 15, 2026: final-01 aborted, empty-netlist fix awaiting full validation

Coordinator: Claude (session ended at a usage limit). Branch
`codex/contract-context`, pushed. `main` frozen at `ca61dbc`; MIT licence added.

**No campaign is running.** `final-01` was stopped after 5 of 360 cells: wiring-only
designs (Prob015_vector1, Prob042_vector4) synthesize to zero cells and the
out-of-context placer fails with "The design is empty" (taxonomy
`empty_netlist_unplaceable`). Its five cells are kept in
`C:/Users/prince.baah/autortl-private/final-01` and must not be rerun there.

**Uncommitted-then-committed in the last commit, NOT fully validated:**
- `autortl/vivado.py`: empty netlist skips place/route; `no_timing_paths.txt`
  marker; `crashed_only_at_exit` (Vivado crashed during shutdown after
  SYNTH_COMPLETE on the empty design). `autortl/report_parser.py`:
  `apply_no_timing_paths`. Tests: `tests/test_empty_netlist.py` (pass).
- Live check was in progress (`empty-live` in the session scratchpad): vector1
  out of context gave real timing WNS 9.002 / WHS 0.385 with 0 LUTs, then the
  exit crash. Constant-output, notgate, chip_top and the three regression
  kinds (ringer, dff, count15) were NOT confirmed. The full test suites were
  NOT rerun after these changes or after the docs cleanup.

**Exact next action**
1. Run the full suites (ROADMAP section 3). Fix anything the cleanup broke.
2. Rerun the live check on Prob015_vector1, Prob002_m2014_q4i, Prob005_notgate,
   Prob036_ringer, Prob031_dff, Prob038_count15 (out_of_context) with
   `autortl.vivado.run_synthesis`; all must return ok with the metrics gate
   passing; archive as `evidence/2026-11-15/empty-netlist-01`.
3. Commit, freeze `final-02` (same 40 tasks, new runtime) with
   `python -m benchmark.pilot manifest`-style code used for final-01 (3 trials),
   run with `python -m benchmark.campaign`, then ROADMAP task B1.
4. Record final-01 as aborted in `docs/BENCHMARK_PILOT.md`.

**Docs cleanup done this session:** one `AGENTS.md`; slim `CLAUDE.md`,
`GEMINI.md`, `START_HERE.md`; README 149 lines with `docs/RESULTS.md` and
`docs/USAGE.md`; superseded docs in `docs/archive/`. ROADMAP tasks D1, D2, D4,
P1 are done; P3 structure is done (numbers wait for B1).

**Environment:** ROADMAP section 3. Keep the machine awake during campaigns.
