
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-05 15:20:26] iter 001 | ACCEPT [NEW BEST]
- In `rx_fifo`, replace `mem[rd_ptr]` output selection with a shift-register queue and drive `out_data` directly from its registered head, keeping that 

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-05 15:35:34] iter 002 | ACCEPT [NEW BEST]
- In `uart_rx_core`, replace the variable bit-select assignment `rx_shift[bit_number - 14'd1] <= majority` with a right shift that inserts `majority` at
