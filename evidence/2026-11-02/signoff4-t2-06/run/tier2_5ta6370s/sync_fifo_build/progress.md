
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 05:12:45] iter 001 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, add a parameterized head-data register and drive `out_data` from it instead of the asynchronous `mem[rd_ptr]` read; update it whe

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 05:14:56] iter 002 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, add a `nonempty` state bit, synchronously clear it on `rst`, and update it from the accepted `push` and `pop` events so it always
