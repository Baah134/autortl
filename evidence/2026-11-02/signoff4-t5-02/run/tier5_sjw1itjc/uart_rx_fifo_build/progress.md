
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 11:07:35] iter 001 | ACCEPT [NEW BEST]
- In `rx_fifo`, replace `out_data = out_valid ? mem[rd_ptr] : 0` with a head-data register that is zero after reset and always reflects the oldest queue

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 11:13:23] iter 002 | ACCEPT [NEW BEST]
- In `uart_rx_core`, change the data-bit update from `data_bits[bit_index - 1'b1] <= majority_vote` to shifting the sampled bit into the byte, such as `

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 11:25:01] iter 003 | REJECT
- In `uart_rx_core`, replace the three repeated pairwise-AND/OR majority expressions with one shared `majority_vote` wire, expressed as `(vote_a & vote_
