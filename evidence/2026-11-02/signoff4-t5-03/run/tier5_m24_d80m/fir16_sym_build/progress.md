
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 12:07:45] iter 001 | ACCEPT [NEW BEST]
- Keep the history update and five-slot ready/valid behavior, but replace the current combinational `acc_wide` through `fir_result` path feeding `data1`

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 12:13:14] iter 002 | ACCEPT [NEW BEST]
- Change only the `rounded4` declaration and the saturation comparisons that use it: represent the rounded value as signed 17-bit data and compare it ag

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 12:18:45] iter 003 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, change the `product_reg` widths and the `sum_a`/`sum_b` and `partial3_a`/`partial3_b` declarations and expressions: use 26-bit si

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-03 12:25:54] iter 004 | REJECT
- In `fir16_sym_core`, replace `C0`–`C7` with their exact halves (`-3, -10, -12, 9, 55, 113, 165, 195`) and narrow the product registers and associated 

<!-- event:20ae74168c1b400f9802e3784c1976a876bb06158d6d7ac441cccf3754c8cfd1 -->
## [2026-11-03 12:31:45] iter 005 | REJECT
- In `fir16_sym_core`, replace the uniform 26-bit `product_reg[0:7]` with per-coefficient signed widths sized for the maximum 17-bit pair sum multiplied

<!-- event:c7deaa336d0458919389c7ecb5e2694c83e32c916bac1ecca211b44f7069bdbe -->
## [2026-11-05 15:21:10] iter 006 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, change only the `rounded_in` rounding pattern: perform `acc_full + 28'sd1024` as a signed 28-bit operation, then assign bits `[27
