# PLAN — iteration 3
## Current state assessment
The verified incumbent uses 19 LUTs and 33 FFs, with timing met at WNS 0.354 ns and WHS 0.024 ns. The objective is strictly fewer LUTs while retaining timing closure. The supplied seed has separate transmit, receive, and response registers; prior accepted iterations reduced LUT use and parameterized the phase counter.

## Hypothesis
Use the transmit shift register to accumulate received bits as each transmitted bit is consumed, removing redundant data storage and potentially reducing LUTs while preserving timing feasibility.

## Instruction for generator
In `spi_master_core`, replace the separate `tx_shift`, `rx_shift`, and `rsp_data_reg` storage with one 8-bit shift register: load `cmd_data` on acceptance, shift left and append `miso` only on the existing rising-SCLK sample edges, and expose that register as `rsp_data`. Keep `mosi` registered and update it only on falling-SCLK edges from the next unsent bit in the shared register; on the final falling edge, retain the completed received byte unchanged through any response stall. Preserve reset, handshakes, all `HALF_PERIOD` timing, and the top’s `// @latency 33` annotation; verify the expected storage savings against routed LUT, WNS, and WHS results.