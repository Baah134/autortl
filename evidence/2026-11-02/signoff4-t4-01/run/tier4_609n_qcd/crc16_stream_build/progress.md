
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 07:14:17] iter 001 | ACCEPT [NEW BEST]
- In `crc16_stream_core`, replace the separate `frame_crc` and `out_crc_reg` storage with one 16-bit CRC register that drives `out_crc` and captures the

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 07:17:19] iter 002 | REJECT
- In `crc16_stream_core`, replace the loop-based `crc16_update` function with explicit, factored XOR equations for the same CRC-16/CCITT-FALSE byte upda

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 07:19:44] iter 003 | ACCEPT [NEW BEST]
- In `crc16_stream_core`, remove `start_of_frame` and use the prior `out_last_reg` value to select `16'hFFFF` as the CRC seed for the next accepted byte
