
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 05:33:50] iter 001 | ACCEPT [NEW BEST]
- Apply Vivado’s `use_dsp = "yes"` attribute to the four product operations that drive `product0` through `product3`, leaving the pair sums, final sum, 

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 05:36:21] iter 002 | REJECT
- Keep the four product operations’ existing `use_dsp = "yes"` attributes and apply the same attribute to the 17-bit `input_partial_lo` and `input_parti

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 05:38:55] iter 003 | ACCEPT [NEW BEST]
- Keep the four multiplier `use_dsp = "yes"` attributes and the iteration 2 input pair-sum implementation; add `(* use_dsp = "yes" *)` to the 18-bit `pa
