---
name: verilog-idioms
description: "Use when generating or fixing any synthesisable Verilog module: FSM structure, latch avoidance, reset discipline, counters, shift registers, handshakes."
---
# Verilog Idioms for Synthesis

## Two-process FSM (the safe pattern)
State register in one sequential block; next-state and outputs in one combinational block with defaults first. See snippets/fsm_two_process.v.

## Latch avoidance
A latch is inferred when a combinational block can exit without assigning a signal. Cure: give every signal a default at the TOP of the block, then override in branches.
```verilog
always @(*) begin
    grant = 1'b0;          // default FIRST
    if (req && !busy) grant = 1'b1;
end
```

## Reset discipline
- Reset every state-holding register. Do not reset large data pipelines unnecessarily (wastes routing); reset control, valid flags, and counters.
- Synchronous reset template:
```verilog
always @(posedge clk) begin
    if (rst) count <= 0;
    else if (enable) count <= count + 1'b1;
end
```

## Valid/ready handshake rules
- A transfer happens on `valid && ready` at a clock edge.
- `valid` must not depend combinationally on `ready` (no combinational loops).
- Once `valid` is high, keep data stable until the beat completes.
See snippets/valid_ready_stage.v.

## Width discipline
- Compare and add at the minimum width mathematics requires; Vivado prunes but explicit narrowing is more reliable and reads clearer.
- Constants: size them (`10'd1000`, not bare `1000`) in comparisons to avoid 32-bit promotion.

## Pipeline register stage
See snippets/pipeline_stage.v — the pattern for adding a cycle of latency cleanly (and remember to update `// @latency`).
