
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 09:19:14] iter 001 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, change the `acc = product0 + ... + product7` accumulation from a serial left-associated sum to an explicitly balanced tree of sig

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 09:30:07] iter 002 | REJECT
- In `fir16_sym_core`, keep the 28-bit `rounded` calculation unchanged and replace the comparisons against `28'sd32767` and `-28'sd32768` with sign-exte

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 09:36:46] iter 003 | REJECT
- In `fir16_sym_core`, replace the `ready4` four-term `acc` assignment with two registered 28-bit partial sums, `sum01 + sum23` and `sum45 + sum67`. In 

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-03 09:42:44] iter 004 | REJECT
- In `fir16_sym_core`, replace the eight full-coefficient product registers with products of the 17-bit pair sums by the half coefficients `-3, -10, -12

<!-- event:20ae74168c1b400f9802e3784c1976a876bb06158d6d7ac441cccf3754c8cfd1 -->
## [2026-11-03 09:50:31] iter 005 | REJECT
- In `fir16_sym_core`, replace the eight 28-bit `product` registers with signed widths 20, 22, 22, 22, 24, 25, 26, and 26 bits, respectively; replace `s

<!-- event:f76bb65dfcaad86c411534efe1897efc64533efa691c1a6a511acc5744161954 -->
## [2026-11-03 09:57:39] iter 006 | REJECT
- In `fir16_sym_core`, replace the recursive `ready5` through `ready1` assignments with equivalent expressions: each `ready_i` is `out_ready` OR any emp

<!-- event:80d43a0aaff527f3aa7860ac094b8f7d5313d8341e4268112d55dca23609f4d0 -->
## [2026-11-03 10:03:04] iter 007 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, replace the recursive `ready5` through `ready1` assignments with equivalent expressions: each `ready_i` is `out_ready` OR any emp
