
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-30 20:15:27] iter 001 | ACCEPT [NEW BEST]
- In `rx_fifo`, replace the combinational `mem[rd_ptr]` output read with a resettable registered head-data value that directly drives `out_data` and is 

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-10-30 20:24:02] iter 002 | ACCEPT [NEW BEST]
- In `uart_rx_core`, replace `next_offset / BIT_TICKS` and `next_offset % BIT_TICKS` with counters for the current bit index and phase, initialized on s

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-10-30 20:28:34] iter 003 | ACCEPT [NEW BEST]
- In `uart_rx_core`, replace `rx_shift[bit_index - 1'b1] <= majority_vote` in the data-bit branch with a right shift that inserts `majority_vote` at bit
