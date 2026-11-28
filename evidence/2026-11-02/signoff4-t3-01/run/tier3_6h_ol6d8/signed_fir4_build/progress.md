
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 05:44:12] iter 001 | ACCEPT [NEW BEST]
- In `signed_fir4_core`, add a synchronous-reset full-occupancy register whose next value tracks whether all three valid slots will be occupied after th

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 05:46:22] iter 002 | REJECT
- Change the FIR arithmetic pattern in `signed_fir4_core`: represent `3*x` and `-2*hist3` as signed 10-bit products, and `-5*hist1` and `7*hist2` as sig

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 05:48:37] iter 003 | REJECT
- In `signed_fir4_core`, keep the existing signed 13-bit `term0` through `term3`, but replace the serial `term0 + term1 + term2 + term3` expression with
