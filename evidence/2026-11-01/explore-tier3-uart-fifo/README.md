# Tier3 uart_fifo_build: four attempts that taught the planner

Exploratory runs, not curriculum verdicts: `tools/explore.py --tier 3 --entries
uart_fifo_build --jobs 1 --model gpt-6-luna`, each on the main checkout after
the fix from the previous attempt. The entry is a prose request (`spec.md`) for
a UART transmitter fed by a FIFO. Earlier attempts: `explore-tier3-02` (spec
lint failed four times on payload tagging) and `explore-tier3-03` (sandbox
refused `state["count"] -= 1`; fixed-latency module with handshake ports found
only at oracle time).

| Run | Code | Outcome | Failure mode found | Fix |
|---|---|---|---|---|
| 04 | c0b15ed4^ (991fec63, cd03b9cd) | spec_lint_failed | A transmitter fed by a FIFO fits neither generated-oracle shape; the planner cycled through three wrong taggings | `one_sided_handshake_has_no_oracle_shape`: prompt and error state the shape that always fits |
| 05 | c0b15ed4 | module_failed | Two oracles both followed the prose (start at once, no valid) and disagreed with the planner's own examples (idle tx=1) | `oracle_example_dispute_ends_build`: disputes go back to the planner |
| 06 | 6b14a8ca | spec_lint_failed | Example errors named no ports; one repair returned a partial spec | `unnamed_example_input_error`, `partial_spec_in_repair` |
| 07 | 5a405549 | build_blocked | **Two live disputes repaired** (sync_fifo, then uart_tx) and every module got agreeing oracles; then blocked because the entry has no integration testbench, which the harness requires for multi-module builds | Curriculum: the entry needs a fixed top interface and an independent, qualified testbench (in progress) |

Each run folder holds the run, its console and a role report
(`tools/role_report.py`). Simulator snapshots and Vivado scratch are not
copied.
