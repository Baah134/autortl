# PLAN — iteration 1
## Current state assessment
The incumbent uses 55 LUTs and 37 FFs on `xc7a35tcpg236-1`; setup slack is 0.494 ns and hold slack is 0.113 ns, so both timing gates currently pass. The objective is strictly fewer LUTs while retaining timing feasibility. The dead `prev_count` register is already absent from the measured FF count, so removing it alone is not a useful area hypothesis. The top’s numeric latency is unknown; preserve the existing observable cycles and do not add a numeric latency annotation.

## Hypothesis
Replacing the explicit all-ones wrap branch with the counter’s natural modulo-`WIDTH` increment and deriving overflow from `&count` may reduce LUT logic while preserving behavior.

## Instruction for generator
In the enabled count update, remove the `count_next` temporary and the `count == {WIDTH{1'b1}}` branch; assign `count <= count + 1'b1` and `overflow <= &count`. Keep reset, load priority, disabled-cycle holds, and all registered threshold flag logic unchanged, including flags’ pre-edge count behavior. Preserve behavior for every supported `WIDTH`, including natural truncation on increment; retain the candidate only if all required verification and routed metric gates pass and LUT use is strictly below 55.