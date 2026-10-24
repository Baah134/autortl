# PLAN — iteration 3
## Current state assessment

Iteration 1 is the verified best at 33 LUTs, 46 FFs, WNS 0.313 ns, and WHS 0.095 ns; it passes the fixed behavioral and implementation gates. Iteration 2 repeated the same proposal and RTL, so it was rejected for no strict LUT improvement, and the watchdog reports churn. The next candidate must make a distinct structural change and use fewer than 33 LUTs while preserving the known 9-cycle behavior and passing every gate.

## Hypothesis

Replacing the binary iteration counter and its increment/terminal-decode logic with a shifting one-hot step token may reduce LUT use by trading additional FFs for simpler control logic.

## Instruction for generator

In `iterative_divider_core`, replace the binary `iteration` counter, its increment, and the `iteration == WIDTH - 1` terminal check with a `WIDTH`-bit one-hot step token: load bit 0 on request capture, shift it once per busy cycle, and use the current top bit to identify the final computation cycle. Handle `WIDTH=1` correctly, and preserve the existing cycle timing, arithmetic, registered outputs, handshakes, reset priority, and `// @latency 9` annotation. Keep the interface and parameter behavior unchanged across supported widths. This is a new experiment; promote it only if the unchanged verification and routed timing gates pass and LUT use is strictly below the 33-LUT incumbent.