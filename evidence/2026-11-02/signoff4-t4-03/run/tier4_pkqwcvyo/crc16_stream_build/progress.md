
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 08:14:10] iter 001 | REJECT
- In `crc16_stream_core`, replace the loop-based `crc16_update` function with explicit parallel Boolean equations for the 16-bit CRC-16/CCITT-FALSE byte

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 08:16:40] iter 002 | ACCEPT [NEW BEST]
- In `crc16_stream_core`, remove `frame_crc` and derive the CRC update state from `out_crc_reg` when the previous accepted byte was not last, or `16'hFF

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 08:19:43] iter 003 | REJECT
- In `crc16_stream_core`, replace `crc_state = out_last_reg ? 16'hFFFF : out_crc_reg` followed by `crc16_update(crc_state, in_data)` with Boolean equati
