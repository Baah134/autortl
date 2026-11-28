# PLAN — iteration 1
## Current state assessment

The incumbent is timing-feasible at WNS 0.579 ns and WHS 0.052 ns, with 8 LUTs and 8 FFs; the objective is to reduce LUTs, and the current one-LUT-per-output-bit mapping appears close to the floor. Top numeric latency is unknown, so no numeric annotation is required; preserve the registered output and synchronous, active-high reset behavior exactly.

## Hypothesis

Sharing a four-way one-hot select decode across the 8-bit datapath may reduce routed LUT use below 8 while retaining the 8 output FFs, though the current mapping may already be optimal.

## Instruction for generator

Replace the `case (sel)` data-selection pattern with shared combinational one-hot decode signals for the four `sel` values and a bitwise masked-OR of `a`, `b`, `c`, and `d` in the existing clocked block. Keep the `if (rst)` branch first and preserve the same registered `y` update on every clock edge. Do not add registers or annotate numeric latency; judge the candidate only after the unchanged simulation and routed metric gates pass, and retain it only if it strictly reduces LUTs against the incumbent.