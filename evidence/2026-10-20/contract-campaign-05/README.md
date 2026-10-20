# Fresh autonomous tier0 campaign05

**2/2 mandatory gates passed; one accepted improvement.** First qualifying
cohort under runtime-bound governance: streak 1, held=false. No recovery or
regrading of earlier failed cohorts was used.

| Design | Baseline / retained best LUTs | FFs | Best setup / hold slack | Calls | Charged tool seconds |
|---|---|---|---|---|---|
| counter | 55 / **53** | 37 | 0.456 / 0.282 ns | 3 | 486.673 |
| mux4 | 8 / **8** | 8 | 0.579 / 0.052 ns | 3 | 381.297 |

Counter candidate passed the frozen independent all-output testbench,
static/structural checks, actual successful subprocess exits, synthesis and
routed reports, deterministic evidence gate and final review (8/8 PASS, ACCEPT).
The 2-LUT reduction is 3.636%, rounded 3.6%. Best_iteration 1 is promoted.
Baseline setup/hold were 0.494/0.113 ns; setup slack decreased but remained positive.
No timing improvement or general parameter equivalence is claimed.

Mux candidate passed behavioral and physical checks (8 LUTs, setup 0.579 ns,
hold 0.057 ns) but had no LUT gain. Review rejected it only for the objective;
best_iteration 0 retained the verified baseline. Unknown numeric source latency
remained explicitly unknown rather than an invented zero-cycle requirement.

## Evidence and provenance

- Vivado 2025.2; xc7a35tcpg236-1; 10 ns; explicit ideal zero minimum/maximum I/O
  delays. One iteration/candidate; 16 model calls, 12 tool minutes, 18 wall minutes
  per design, one infrastructure retry. Measurements are specific to this setup.
- Complete runtime bytes were tested by 655 passing regression tests. Launched
  over 71910e5 with the already-tested conventions file unstaged; 5d285c0 then
  published that same file. No runtime bytes changed during the campaign. All
  actual runtime manifests match the test identities and published source.
- Raw tool receipts distinguish actual process and driver exits, retain process
  IDs/durations and complete output hashes. Candidate process_exit_gate passed.
  Verification input manifests bind actual simulated sources and testbenches.
- Actual CLI DONE replay of counter returned the same accepted winner, with
  unchanged budget/summary/winner hashes and no added model or tool calls.
  counter_done_replay_* records retain this separate check. It does not prove
  in-flight/hard-kill recovery.
- Sources, trusted TBs, task metadata, raw reports, evaluation facts/decisions,
  budgets, state/journal metadata and runtime identity are retained. Compiled
  artifacts and duplicated journal artifact trees are omitted. Some raw
  sidecars/logs reference those original machine-local paths; archive manifests
  identify the retained subset without pretending it is a resumable run folder.

Model identity was not exposed by the CLI. This is one bounded autonomous gain,
not a weaker-model study or a held tier. Prior 0/2, 0/2, 1/2 and 2/2 cohorts remain
separate in their archives. They cannot be silently removed or supply this
new runtime-bound streak. See reproduction.json; use a fresh output directory.
