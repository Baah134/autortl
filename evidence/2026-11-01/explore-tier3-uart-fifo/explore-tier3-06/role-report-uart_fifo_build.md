# Role report

| Run | Status | Model calls | Tokens in / out | Baseline LUT | Best LUT | Evaluator verdicts | Repairs |
|---|---|---:|---:|---:|---:|---|---|
| uart_fifo_build | spec_lint_failed | 4 | 74,051 / 14,778 | — | — | — | planner spec attempts 4 |

## uart_fifo_build: spec_lint_failed
- error: protocol mismatch: sync_fifo.in_ready (valid_ready) -> uart_tx.load (none)
- error: module sync_fifo: example 0: inputs must contain only declared non-clock input ports
- error: module sync_fifo: example 0: expected must cover exactly all data output ports and be nonempty (data outputs are the protocol none outputs: ['out_data']; tag only valid/ready handshake ports valid_ready, payload ports none)
- error: module sync_fifo: example 1: inputs must contain only declared non-clock input ports
- error: module sync_fifo: example 1: expected must cover exactly all data output ports and be nonempty (data outputs are the protocol none outputs: ['out_data']; tag only valid/ready handshake ports valid_ready, payload ports none)
- error: module uart_tx: example 0: inputs must contain only declared non-clock input ports
- error: module uart_tx: example 1: inputs must contain only declared non-clock input ports

| Role method | Completed | Unfinished | Retries |
|---|---:|---:|---:|
| planner.make_spec | 4 | 0 | 0 |
