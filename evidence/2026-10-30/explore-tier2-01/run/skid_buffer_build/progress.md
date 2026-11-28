
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-30 11:08:06] iter 001 | ACCEPT [NEW BEST]
- Replace the `skid_buffer_core` instance with inline two-entry FIFO logic using head and tail data registers plus occupancy state; assign `out_data` di

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-10-30 11:11:31] iter 002 | ACCEPT [NEW BEST]
- In `skid_buffer`, replace the two-bit `occupancy` state and its case-based updates with `head_valid` and `tail_valid` bits, deriving `out_valid` from 
