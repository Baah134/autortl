
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 05:03:29] iter 001 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace `storage[0:1]` and `read_ptr`-based output selection with an explicit front register that drives `out_data` and a back 

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 05:05:48] iter 002 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace `occupancy` with two valid bits for the front and back entries, using only legal states for empty, one-word, and full; 
