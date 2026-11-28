
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-30 19:33:10] iter 001 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, replace the combinational path from the eight symmetric pair sums through `acc`, rounding, and saturation into `data1` with stage

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-10-30 19:41:47] iter 002 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, add a synchronous `full_q` flag that remains equal to `&valid_slots`: clear it on reset and update it each cycle from the next va

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-10-30 19:58:44] iter 003 | REJECT
- In `fir16_sym_core`, change stage 1 to register `pair0` through `pair7` when `ready1` and `in_valid`, and form the eight constant products from those 
