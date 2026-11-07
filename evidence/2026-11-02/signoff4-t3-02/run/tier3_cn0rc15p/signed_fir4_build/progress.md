
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 06:18:15] iter 001 | ACCEPT [NEW BEST]
- Replace the combinational `!v1 || !v2 || !v3` vacancy calculation with a resettable register that tracks whether any elastic slot is vacant, updating 

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 06:20:27] iter 002 | REJECT
- Keep the registered vacancy tracking introduced in iteration 1, but change the `in_ready`/`r1` logic so the external `in_ready` signal is driven direc

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 06:22:45] iter 003 | ACCEPT [NEW BEST]
- In `signed_fir4_core`, replace `term0` through `term3` and the serial `fir_result` expression with explicit 13-bit signed shift-add terms for `3*x`, `
