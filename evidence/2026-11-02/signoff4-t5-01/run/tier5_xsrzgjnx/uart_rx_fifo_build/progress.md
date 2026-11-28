
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 09:44:48] iter 001 | ACCEPT [NEW BEST]
- In `rx_fifo`, replace the `mem[rd_ptr]` combinational output selection with an `out_data` register that is zero after reset, loads `wr_data` on a push

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 09:50:40] iter 002 | REJECT
- In `uart_rx_core`, replace the fixed 14-bit `frame_offset` and its dependent `elapsed_next` width with a parameter-derived width sufficient to represe

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 09:56:47] iter 003 | ACCEPT [NEW BEST]
- In `uart_rx_core`, replace the `frame_data[bit_index - 1'b1] <= majority` variable-index write in the data-bit decision branch with a right shift that
