# PLAN — iteration 1
## Current state assessment
The baseline passes simulation and is timing-feasible on xc7a35tcpg236-1 at 10 ns: 55 LUTs, 37 FFs, WNS 0.494 ns, and WHS 0.113 ns. The objective is strictly fewer LUTs while retaining all verification and routed metric gates. Top numeric latency is unknown; preserve its observable cycle behavior without inventing a latency annotation.

## Hypothesis
Using the increment adder’s carry-out as the wrap detector should remove the separate all-ones comparison and count-reset selection, reducing LUT use while preserving counter and overflow behavior.

## Instruction for generator
Replace the increment branch’s `count_next` assignment, full-width all-ones comparison, and special count reset with a `WIDTH+1`-bit `count + 1` result; load its low `WIDTH` bits into `count` and use its carry bit for `overflow`. Preserve reset-over-load-over-enable priority, overflow hold while disabled, and registered threshold flags computed from the pre-edge count. Preserve behavior for supported `WIDTH` and threshold parameters, including `WIDTH=1`, high-bit values, wraparound, simultaneous load and enable, and synchronous reset.