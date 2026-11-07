
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 02:11:51] iter 001 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, keep the circular storage and occupancy behavior, but add a `WIDTH`-bit head register that directly drives `out_data`; load it fr

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 02:14:21] iter 002 | ACCEPT [NEW BEST]
- Specialize `sync_fifo_core` for `DEPTH==3` to use three `WIDTH`-bit entry registers, with entry 0 driving `out_data`; shift entries on pop and place a
