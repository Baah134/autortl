
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 20:50:50] iter 001 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, replace the dynamically indexed `memory[read_ptr]` output path with a dedicated head register that directly drives `out_data`; up

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 20:59:39] iter 002 | ACCEPT [NEW BEST]
- In `sync_fifo_core`, change the full-depth `memory` ring so it stores only queued words behind `head`; write the tail on pushes into a nonempty FIFO, 
