
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 01:25:33] iter 001 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace `storage[0:1]` plus `read_ptr`-indexed `out_data` with explicit head and tail data registers, and drive `out_data` dire

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 01:28:03] iter 002 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace the 2-bit `occupancy` state and its increment/decrement case with synchronous `empty` and `full` flags updated for rese
