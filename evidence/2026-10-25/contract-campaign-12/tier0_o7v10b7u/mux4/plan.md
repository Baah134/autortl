# PLAN — iteration 1

## Current state assessment

The 8-bit registered 4:1 mux has synchronous active-high reset and no parameters. The incumbent uses 8 LUTs and 8 FFs and meets timing at 10 ns (WNS 0.579 ns, WHS 0.052 ns), so this is a LUT-reduction attempt, not timing recovery. The current top’s numeric latency is unknown; preserve its cycle behavior and do not add a latency annotation. Since the existing mapping already uses one LUT per output bit, reducing LUTs below 8 may be difficult.

## Hypothesis

Rewriting the `case` as an explicit nested ternary mux may let Vivado map the selection and synchronous reset into fewer than 8 LUTs while retaining 8 output FFs and nonnegative setup and hold slack.

## Instruction for generator

Replace only the `case (sel)` selection with nested ternary expressions for the four inputs; keep the existing clocked process and synchronous `rst` priority unchanged. Preserve the registered `y` update on every rising edge, all four `sel` mappings, and reset-to-zero behavior. Judge the hypothesis using the frozen testbench and retained routed reports; promote only if every gate passes and LUT usage is strictly below 8.