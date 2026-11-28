
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 07:43:38] iter 001 | REJECT
- Replace the loop-based `crc16_update` function with explicit, factored GF(2) XOR equations for the same 16-bit state and 8-bit data inputs, preserving

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 07:45:58] iter 002 | ACCEPT [NEW BEST]
- In `crc16_stream_core`, remove `frame_crc` and use `out_crc_reg` as the input state to `crc16_update` on each accepted byte; after `in_last`, select `

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 07:49:00] iter 003 | REJECT
- In `crc16_stream_core`, change the `crc_seed` / `crc_next` logic so the CRC update is expressed using CRC linearity: separate the data contribution an
