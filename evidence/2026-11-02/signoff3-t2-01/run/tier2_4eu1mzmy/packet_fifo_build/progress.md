
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 20:35:53] iter 001 | ACCEPT [NEW BEST]
- In `packet_fifo_core`, replace the integer `occupancy` with a counter sized for values 0 through `DEPTH`, and maintain a `full` register that tracks w

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 20:40:17] iter 002 | ACCEPT [NEW BEST]
- In `packet_fifo_core`, replace the `integer read_ptr` and `integer write_ptr` declarations with unsigned vectors sized to represent indices `0` throug

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 20:51:02] iter 003 | REJECT
- In `packet_fifo_core`, replace `occupancy` with a `full` register: derive empty from `read_ptr == write_ptr` and `!full`, use `!full || out_ready` for
