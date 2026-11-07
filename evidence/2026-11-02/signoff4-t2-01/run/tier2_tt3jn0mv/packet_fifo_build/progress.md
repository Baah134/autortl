
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 01:11:16] iter 001 | ACCEPT [NEW BEST]
- In `packet_fifo_core`, add head data and last registers and drive `out_data` and `out_last` directly from them; update the cached tuple on an empty pu

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 01:13:39] iter 002 | ACCEPT [NEW BEST]
- In `packet_fifo_core`, keep the cached head tuple and occupancy logic, but add registered empty and full flags that track the current occupancy and dr

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 01:18:26] iter 003 | REJECT
- In `packet_fifo_core`, keep the registered `head_data` and `head_last` outputs, but replace `data_mem` and `last_mem` with a tail of `DEPTH-1` tuples 
