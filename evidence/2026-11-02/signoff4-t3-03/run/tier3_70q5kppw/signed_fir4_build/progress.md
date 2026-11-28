
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 06:50:59] iter 001 | ACCEPT [NEW BEST]
- In `signed_fir4_core`, replace the cascaded `r3`/`r2`/`r1` readiness calculation for `in_ready` with a registered flag that tracks whether all three s

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 06:53:02] iter 002 | ACCEPT [NEW BEST]
- In `signed_fir4_core`, replace the 13-bit sign-extended operands and wide multiply/add chain in `fir_result` with explicitly sized signed intermediate

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 06:57:18] iter 003 | REJECT
- In `signed_fir4_core`, remove `full`, its reset and sequential updates, and the `v1_next`/`v2_next`/`v3_next` lookahead used only to update it. Derive
