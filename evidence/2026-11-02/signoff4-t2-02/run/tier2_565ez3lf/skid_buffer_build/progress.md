
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 02:04:10] iter 001 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace the `storage[read_ptr]` indexed output with explicit 8-bit head and tail registers, and drive `out_data` directly from 

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 02:06:34] iter 002 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, recode occupancy control as `head_valid` and `tail_valid` flags: drive `out_valid` from `head_valid`, `in_ready` as `!tail_vali
