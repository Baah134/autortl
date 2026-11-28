
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 20:31:03] iter 001 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace the combinational `out_valid = (occupancy != 0)` output with a dedicated register that is reset synchronously to zero a

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 20:35:22] iter 002 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace the binary `occupancy` counter and separate `out_valid_reg` with two state registers: `nonempty` drives `out_valid`, an
