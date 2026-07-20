---
name: timing-closure
description: "Use when a design fails timing (negative WNS): reading the failing path, choosing between pipelining, fanout replication, retiming, and constraint fixes."
---
# Timing Closure Playbook

## Read the path first
A failing path has: startpoint FF, endpoint FF, logic levels, net delays, slack. Two numbers decide the cure:
- **Logic levels >= 8** → too much combinational depth → PIPELINE (insert a register mid-path; update `// @latency`).
- **Any net fanout >= 64** → replication (duplicate the driving FF; split loads) or `set_max_fanout`.

## Escalation order (cheapest first)
1. **Tool knobs (zero code risk):** `synth_design -retiming`, `phys_opt_design` after place. Rescues deficits down to about -0.5 ns.
2. **RTL surgery:** pipeline insertion or fanout replication per the categories above. For -0.5 to -3 ns.
3. **Replan:** worse than -3 ns usually means the architecture is wrong (e.g. single-cycle wide multiply at 200 MHz) — change structure, not lines.

## Pipelining rules
- Cut the path roughly in half; a register that moves the cut off the critical path does nothing.
- Balance parallel branches — every path through the cut gains exactly one cycle.
- Valid signals pipeline alongside data.

## Fanout replication
```verilog
(* max_fanout = 32 *) reg enable_r;    // or physically duplicate:
reg en_a, en_b;
always @(posedge clk) begin en_a <= en; en_b <= en; end
```

## What NOT to do
- Don't demote timing DRCs.
- Don't add false-path constraints to "fix" real paths.
- Don't pipeline without updating the declared latency (contract law).
