# PLAN — iteration 1
## Current state assessment

The verified baseline uses 55 LUTs and 37 FFs on xc7a35tcpg236-1, with routed WNS 0.494 ns and WHS 0.113 ns; simulation passes. The objective is strictly fewer LUTs, while preserving the exact observable behavior. Numeric latency is unknown, so preserve the existing cycle behavior without adding an annotation. Promotion still requires the unchanged verification gates, valid routed metrics, and nonnegative setup and hold slack.

## Hypothesis

Removing the wrap-specific count selection should reduce LUT use because WIDTH-bit addition already wraps to zero at all ones, while retaining the existing overflow behavior and timing closure.

## Instruction for generator

In the sequential counter update, replace the `count_next` assignment and the `count == {WIDTH{1'b1}}` branch that selects between zero and `count_next` with a direct `count <= count + 1'b1` on enabled increments. Set `overflow` to the all-ones comparison only in the enabled increment branch, preserving its hold behavior when disabled. Keep reset-over-load-over-enable priority, load clearing overflow, and all registered threshold flags unchanged.