# Durable task board

Inspect Git and the local coordination status before claiming work. A task
marked in progress may contain saved changes from an interrupted coordinator.
Do not overwrite them. Live claims use scripts/session.py; this board travels
with Git and states acceptance criteria.

| Task | Status | Completion evidence / remaining acceptance |
|---|---|---|
| Codex runtime and generated counter | Published | Commit 68fc5e6; 226 tests at checkpoint; generated 8-bit counter passed simulation, mutation checks and routing |
| Relocate canonical clone | Complete | Downloads/autortl-work; 317 source/Git file hashes matched before and after move |
| Provider-neutral shared memory | Published | 8d5eb09; lease/task/handoff CLI; concurrency/ownership and full-suite tests; checkpoint retains active coordinator |
| Atomic config/state/budget/cache | Tested | Strict persistence, cache provenance and integrated FSM recovery tests pass |
| Generated TB timing and handshake | Implemented, tested live | All 9 Vivado cases behaved as expected; retain logs and hashes |
| Restricted golden execution | Tested | Child process, AST restrictions and resource limits tested; remaining allocation limits documented in RECOVERY.md |
| Exact Verilog interfaces/static checks | Implemented | 23 focused tests pass; parameterized counter and grouped mux covered |
| Recoverable optimize/build FSM | Tested with controlled tools | Interruption, DONE replay, config/report/source drift, budgets, infra retries and build integration tests pass; live campaign next |
| Curriculum governance and fixtures | Tested | Three matching full cohorts and mandatory gates covered; no newly held tier claimed |
| First live counter/mux campaign | Recorded: 0/2 | Counter baseline 54 LUTs/37 FFs, WNS 5.491 ns; model budget/timescale failure; mux boundary timing missing; no tier held |
| Live regression repairs | Validated, publishing | 423 tests pass; counter replay passes; mux simulation/routing passes: 8 LUTs/8 FFs, WNS 0.579 ns, WHS 0.052 ns; all failed attempts retained |
| Fresh model-driven tier0 campaign | Pending | Authoritative contract context, fresh baselines under explicit I/O assumptions, bounded calls/time; accepted candidate required |
| Build counter8 and priority encoder | Pending | Typed specs, independent module and top tests, negative tests, routed results |

The active coordinator continues with bounded live campaigns after publication.
Do not treat the previously verified standalone generation trial or controlled
unit tests as proof of the complete live build/resume/optimization loop.
