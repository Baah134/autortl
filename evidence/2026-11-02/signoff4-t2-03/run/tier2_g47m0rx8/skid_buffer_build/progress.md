
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 02:47:51] iter 001 | ACCEPT [NEW BEST]
- Replace the combinational `out_valid = (occupancy != 0)` decode with an `out_valid` register, reset synchronously to zero and updated from the pre-edg

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 02:50:32] iter 002 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace the 2-bit `occupancy` state with a `full` flag and reuse `out_valid_reg` as the registered nonempty flag; drive `in_rea
