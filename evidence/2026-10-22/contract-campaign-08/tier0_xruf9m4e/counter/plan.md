# PLAN — iteration 1
## Current state assessment
The baseline passes simulation and has positive routed setup and hold slack (WNS 0.494 ns, WHS 0.113 ns), so timing is feasible. The objective is strictly fewer than 55 LUTs while retaining timing feasibility and passing every verification and metric gate. The top’s numeric latency is unknown; preserve its observable cycles without adding a latency annotation. The I/O delay advisory does not authorize changing constraints.

## Hypothesis
Removing the redundant all-ones count wrap branch should reduce LUT use by letting the `WIDTH`-bit incrementer wrap naturally, while the existing comparison continues to generate the overflow flag.

## Instruction for generator
In `counter`, replace the enabled-count branch’s all-ones conditional and `count_next` temporary with an unconditional `count <= count + 1'b1`; retain the all-ones test for `overflow`. Remove the unused `prev_count` register and its assignments. Preserve reset-over-load-over-enable priority, overflow hold while disabled and clear on load, and registered threshold flags computed from the pre-edge count, including for parameterized widths and thresholds. Do not add latency or a numeric top annotation; retain the fixed interface and compile boundary.