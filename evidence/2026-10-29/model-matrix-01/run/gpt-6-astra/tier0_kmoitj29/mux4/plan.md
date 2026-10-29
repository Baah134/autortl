# PLAN — iteration 1

## Current state assessment

The verified incumbent uses 8 LUTs, 8 FFs and no DSP48 or BRAM, with routed WNS 0.579 ns and WHS 0.052 ns at 100 MHz on xc7a35tcpg236-1. A four-input mux requires six Boolean inputs per output bit, making one LUT6 per bit already an efficient mapping; substantial LUT savings are unlikely. The seed registers all eight selected bits on each rising `clk` edge, with synchronous active-high reset taking priority. Numeric top latency is UNKNOWN; leave its annotation absent while preserving these cycles. Promotion requires fewer than 8 routed LUTs, unchanged constraints, nonnegative setup and hold slack, all behavioral/interface and independent-reference gates, successful tool exits, `SYNTH_COMPLETE`, the exact standalone `TEST PASSED` verdict, valid retained metrics and receipts, and evaluator ACCEPT with zero failed criteria. The frozen testbench alone does not establish equivalence.

## Hypothesis

Explicitly separating combinational selection from the existing output register may improve synthesis factoring, but the expected mapping remains approximately 8 LUTs and 8 FFs, and any result of 8 or more LUTs falsifies the LUT-saving hypothesis.

## Instruction for generator

Replace the sequential `else case (sel)` pattern with a combinational eight-bit selected-data signal using the same plain case mapping and default-to-`d` behavior, followed by the existing rising-edge register assignment. Assign combinational defaults before branches, retain synchronous reset priority and all eight output registers, and introduce no pipeline stages, enables, primitives or numeric latency annotation. Preserve selection behavior for unknown selector values and propagation of selected data, including high bits, while leaving the interface and clock unchanged. Review equivalence against the frozen source across reset transitions and consecutive selections using the existing independent verification framework; retain the incumbent if this bounded experiment produces no accepted LUT reduction.