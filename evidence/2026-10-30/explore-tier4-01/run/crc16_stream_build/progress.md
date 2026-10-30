
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-10-30 12:16:24] iter 001 | REJECT
- Replace the `crc16_stream_core` instance with top-level state and slot logic, and implement the byte update as a factored parallel XOR network for the

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-10-30 12:20:07] iter 002 | REJECT
- Replace the wrapper instance with equivalent top-level slot and CRC state logic, preserving the one-slot ready equation, synchronous active-high reset

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-10-30 12:23:27] iter 003 | REJECT
- In the editable top, replace the separate `frame_crc` and `out_crc_reg` state with one 16-bit CRC register, using it for both the registered output pa
