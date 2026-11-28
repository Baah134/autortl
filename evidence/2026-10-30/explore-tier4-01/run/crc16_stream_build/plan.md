# PLAN — iteration 3
## Current state assessment
The incumbent is timing-feasible at 16 LUTs, so acceptance requires a strict LUT reduction. Iterations 1 and 2 both kept LUT usage at 16 after replacing the child instance with equivalent top-level CRC and slot logic; another CRC-network rewrite alone would repeat the failed objective.

## Hypothesis
Reuse the registered output CRC as the running frame state and use the retained last flag to select the next frame’s initial value, removing the separate 16-bit frame-state register and potentially reducing LUT usage.

## Instruction for generator
In the editable top, replace the separate `frame_crc` and `out_crc_reg` state with one 16-bit CRC register, using it for both the registered output payload and the running CRC; derive the next update’s base as `16'hFFFF` after a last byte and otherwise the stored CRC. Initialize the CRC register to `16'hFFFF` and the last flag to `1` on synchronous reset so the first accepted byte starts from the required initial value; keep the one-slot ready equation, valid/ready replacement behavior, output stability while stalled, reset priority, and `// @latency 1`. The CRC and last payload are unspecified while `out_valid` is low, so use that state reuse only within those unspecified cycles; measure routed LUTs and require strict reduction while all verification and timing gates pass.