
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 04:52:33] iter 001 | ACCEPT [NEW BEST]
- Replace the asynchronous `data_mem[read_ptr]` and `last_mem[read_ptr]` output selection with a registered head tuple and shift-register tail storage, 

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 04:55:30] iter 002 | REJECT
- In `packet_fifo_core`, remove the `not_full` register and its reset and next-state updates; derive `in_ready` as `(occupancy < DEPTH) || out_ready`, p

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 04:58:29] iter 003 | REJECT
- In `packet_fifo_core`, change only the variable-index writes to `tail_data` and `tail_last` into per-slot updates using constant slot indices and occu
