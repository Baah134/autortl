
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 02:58:15] iter 001 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, replace `integer rd_ptr`, `integer wr_ptr`, and `integer occupancy` with unsigned registers sized for the supported `DEPTH` range

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 03:01:24] iter 002 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, replace the binary `occupancy` counter and `(occupancy < DEPTH)` comparison with a parameterized one-hot occupancy state for coun
