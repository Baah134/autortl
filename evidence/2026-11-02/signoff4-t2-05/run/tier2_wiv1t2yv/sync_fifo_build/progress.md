
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 04:29:49] iter 001 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, replace the dynamically indexed memory read with a register array whose entries hold queued words in order: shift entries toward 

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 04:31:54] iter 002 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, replace the combinational `assign out_valid = (occupancy != 0)` with a resettable `valid_reg` that directly drives `out_valid`, u
