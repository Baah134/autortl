
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 17:12:08] iter 001 | ACCEPT [NEW BEST]
- Change only the `y_out` sum pattern: form four pairwise sums of `p0`–`p7`, then two sums of those results, then a final sum, keeping every intermediat

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 17:18:05] iter 002 | ACCEPT [NEW BEST]
- Keep the eight products and their DSP inference, but replace the `s01` through `sum` addition tree with staged 32-bit 3:2 carry-save compressors: each

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 17:23:34] iter 003 | REJECT
- Change only the `sum = s4a + c4a` final adder pattern: divide the 32-bit addition into small fixed-width segments, compute each segment’s sum for carr

<!-- event:63ce19e07823e315e8501a7bcac7fc46b9310a5a9bcecf053b8f5995c10102c7 -->
## [2026-11-02 17:29:18] iter 004 | ACCEPT [NEW BEST]
- Keep the eight signed 32-bit products and the final `s4a + c4a` adder, but replace only the current `s1a`–`c4a` compressor grouping with a balanced Wa

<!-- event:20ae74168c1b400f9802e3784c1976a876bb06158d6d7ac441cccf3754c8cfd1 -->
## [2026-11-02 17:34:26] iter 005 | REJECT
- Keep the `// @latency 1` annotation and change only the product-register and `y_out` accumulation pattern: for each pair `(C0,C7)`, `(C1,C6)`, `(C2,C5

<!-- event:c7deaa336d0458919389c7ecb5e2694c83e32c916bac1ecca211b44f7069bdbe -->
## [2026-11-02 17:37:20] iter 006 | ACCEPT [NEW BEST]
- Keep the eight signed 32-bit product registers and their multiplication assignments unchanged; do not pre-add raw samples or alter the product-registe
