# PLAN — iteration 4

## Current state assessment
Iteration 2 is the verified best at 3 LUTs and 4 FFs with positive setup and hold slack; iteration 3 tied those resources and was rejected for no strict objective gain. The current seed uses a 3-bit binary run counter plus registered `clean`, and the known top latency requires `// @latency 0`.

## Hypothesis
A 3-bit Gray-code phase counter may map its advance and terminal logic to fewer LUTs than the binary increment-and-compare pattern while retaining the four-register state.

## Instruction for generator
Keep the top interface and `// @latency 0`, and retain registered `clean` with a 3-bit phase register. Replace binary increment and the `run_count == 3'd7` terminal branch with an explicit 8-state Gray-code cycle starting at `000`, advancing once per sample where `noisy != clean_reg`, and returning to `000` when the eighth differing sample updates `clean_reg`; when `noisy == clean_reg`, reset the phase to `000`. Preserve synchronous active-high reset and exact sample timing, then evaluate against the 3-LUT, 4-FF incumbent under every required verification and routed timing gate.