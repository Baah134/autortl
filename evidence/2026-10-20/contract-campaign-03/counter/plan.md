# PLAN — iteration 1
## Current state assessment
The verified baseline uses 55 LUTs and 37 FFs, with routed setup slack of 0.494 ns and hold slack of 0.113 ns on the xc7a35tcpg236-1 at a 10 ns clock. The objective is to reduce LUTs; promotion still requires the fixed interface and cycle behavior, all simulation and implementation gates, valid routed metrics, and nonnegative setup and hold slack. The counter’s increment path explicitly checks for all ones before assigning the incremented count, while the registered flags and their one-cycle relationship to `count` are part of the contract.

## Hypothesis
Replacing the all-ones wrap branch with the naturally wrapping `WIDTH`-bit increment should remove redundant wrap-selection logic and reduce LUT use while preserving count and overflow behavior.

## Instruction for generator
In the sequential counter update, remove the `count_next` temporary and the `count == {WIDTH{1'b1}}` branch; when `enable` is active and `load` is not, assign `count <= count + 1'b1` and set `overflow` to the reduction-AND of the pre-edge `count`. Keep reset above load above enable, preserve overflow hold while disabled and clear it on load, and leave the registered flag logic unchanged. Preserve the module interface, parameters, reset behavior, and all observable cycle timing.