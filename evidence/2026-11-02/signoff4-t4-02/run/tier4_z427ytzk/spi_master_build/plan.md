# PLAN — iteration 3
## Current state assessment
Iteration 1 is the verified best at 27 LUTs and 36 FFs, with timing met; iteration 2 was rejected because its 28 LUTs did not improve the objective. The seed already reflects the accepted receive-data-register removal, so this plan targets a different pattern. Keep the top annotation at `// @latency 33` and preserve the fixed cycle behavior and all verification gates.

## Hypothesis
Using the transmit shift register’s MSB as the registered MOSI output can remove the separate `mosi_reg` flip-flop and its update logic, with a possible LUT reduction and no added latency.

## Instruction for generator
In `spi_master_core`, remove `mosi_reg` and drive `mosi` from `tx_shift[7]`; load `cmd_data` into `tx_shift` on command acceptance, then shift it left only on the existing falling-SCLK events. Clear `tx_shift` on reset and transfer completion so MOSI is zero when idle, including while a response is held. Preserve the existing bit order, SCLK schedule for every supported `HALF_PERIOD`, handshakes, reset behavior, and top latency annotation; retain this candidate only if all gates pass and it strictly improves the incumbent LUT/FF objective.