# Durable task board

Inspect Git and the local coordination status before claiming work. A task
marked in progress may contain saved changes from an interrupted coordinator.
Do not overwrite them. Live claims use scripts/session.py; this board travels
with Git and states acceptance criteria.

| Task | Status | Completion evidence / remaining acceptance |
|---|---|---|
| Codex runtime and generated counter | Published | Commit 68fc5e6; 226 tests at checkpoint; generated 8-bit counter passed simulation, mutation checks and routing |
| Relocate canonical clone | Complete | Downloads/autortl-work; 317 source/Git file hashes matched before and after move |
| Provider-neutral shared memory | Tested, publishing | Lease/task/handoff CLI; concurrency/ownership and full-suite tests; checkpoint retains active coordinator |
| Atomic config/state/budget/cache | Tested | Strict persistence, cache provenance and integrated FSM recovery tests pass |
| Generated TB timing and handshake | Implemented, tested live | All 9 Vivado cases behaved as expected; retain logs and hashes |
| Restricted golden execution | Tested | Child process, AST restrictions and resource limits tested; remaining allocation limits documented in RECOVERY.md |
| Exact Verilog interfaces/static checks | Implemented | 23 focused tests pass; parameterized counter and grouped mux covered |
| Recoverable optimize/build FSM | Tested with controlled tools | Interruption, DONE replay, config/report/source drift, budgets, infra retries and build integration tests pass; live campaign next |
| Curriculum governance and fixtures | Tested | Three matching full cohorts and mandatory gates covered; no newly held tier claimed |
| Live full harness counter/mux campaign | Pending | Bounded model/tool budgets, matching source/report hashes, honest no-improvement outcome if appropriate |
| Build counter8 and priority encoder | Pending | Typed specs, independent module and top tests, negative tests, routed results |

The active coordinator continues with bounded live campaigns after publication.
Do not treat the previously verified standalone generation trial or controlled
unit tests as proof of the complete live build/resume/optimization loop.
