
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 03:42:56] iter 001 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, add a head-data register and replace the asynchronous `mem[rd_ptr]` output with a direct connection from that register; update it

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 03:47:44] iter 002 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, change the current full-depth `mem` organization into a registered head plus a circular buffer for only `DEPTH-1` tail entries; h
