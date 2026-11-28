
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 03:33:14] iter 001 | ACCEPT [NEW BEST]
- In `skid_buffer_core`, replace `reg [1:0] count` and the `case (count)` occupancy control with head-valid and tail-valid state; derive `out_valid` fro

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 03:35:48] iter 002 | REJECT
- In `skid_buffer_core`, replace the nested occupancy branches that update `head_valid` and `tail_valid` with direct next-state equations derived from `
