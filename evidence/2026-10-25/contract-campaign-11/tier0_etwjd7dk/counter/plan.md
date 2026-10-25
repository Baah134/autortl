# PLAN — iteration 1

## Current state assessment

The counter already passes the fixed simulation and has routed setup/hold slack of 0.494 ns/0.113 ns, with 55 LUTs and 37 FFs on the xc7a35tcpg236-1 at a 10 ns clock. The top’s numeric latency is unknown, so do not add a numeric latency annotation. The objective is strictly fewer LUTs while retaining timing feasibility and every defined cycle behavior.

## Hypothesis

Removing the unused `prev_count` state and redundant `count_next` temporary should preserve behavior and may reduce mapped logic, though LUT savings are uncertain because synthesis may already eliminate both.

## Instruction for generator

Remove the never-read `prev_count` register and its reset/update assignments. Replace the blocking `count_next = count + 1'b1` temporary with direct next-count assignment while preserving the all-ones wrap check, overflow behavior, and reset > load > enable priority. Keep the registered threshold flags and their pre-edge count semantics unchanged; preserve behavior for supported `WIDTH` and threshold parameter values.