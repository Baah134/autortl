# AutoRTL evidence — 2026-10-21

| Experiment | Result and source |
|---|---|
| [Recovery tests](fifo-recovery-tests/) | 939 full tests; bounded repair, timing policy, UTF-8 and original child identities; source49599b5 |
| [FIFO02](generated-fifo-attempt-02/) | Source49599b5; sleep/timeout and exhausted budget; no accepted physical result |
| [FIFO03](generated-fifo-attempt-03/) | Source49599b5; functional passes, failed setup and exhausted budget; feedback-gap proof retained |
| [FIFO04](generated-fifo-attempt-04/) | Sourced39e34d; candidate closed timing but false top-annotation requirement rejected it; original baseline retained |
| [Feedback context tests](feedback-context-tests/) | Final984 tests; report-linked paths, resolved build semantics, rejected trial feedback and proven no-op skip |

Each experiment retains its own source, budgets, metrics, original paths and
hash manifest. Failures remain failures. No weak-model or all-parameter proof
is claimed. Compiled trees and journal copies may be omitted; read each archive
README before attempting reproduction. New physical/campaign results follow
only after fresh runs on the tested runtime.
