---
name: verilog-idioms
description: "Contract-preserving verilog-idioms guidance for AutoRTL."
---
# Verilog Idioms for Synthesis

## Preserve the fixed contract
Preserve exact cycle latency, registered outputs, reset/enable priority,
parameter behavior, signedness and high bits. An `@latency` edit cannot authorize
extra cycles. Retiming existing registers requires identical observable behavior.

## Combinational and sequential logic
Give every combinational output a default before conditional overrides to avoid
latches. Use one driver per signal, nonblocking assignments in clocked blocks,
and blocking assignments in combinational blocks. A two-process FSM is useful
only if its output registration matches the contract; see snippets/fsm_two_process.v.
Reset every register the contract requires, with its exact polarity and kind.
Do not remove resets for inference or add resets that change specified behavior.

## Width discipline
Compute explicit operand/result widths and signedness before narrowing. Prove
that discarded high bits cannot affect any supported input or parameter value.
Size constants without truncating thresholds; preserve overflow/wrap semantics.

## Handshakes
Transfer occurs on valid && ready at the active clock edge. Keep valid/data
stable while stalled, as specified. Avoid combinational handshake loops.
See snippets/valid_ready_stage.v; adapt only within the fixed contract.
The pipeline_stage.v example has a fixed two-cycle contract; it is not permission
to add a stage to an existing design.
