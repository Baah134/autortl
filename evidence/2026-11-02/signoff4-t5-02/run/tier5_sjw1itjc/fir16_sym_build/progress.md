
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 10:51:05] iter 001 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, replace `(acc + 28'sd1024) >>> 11` with the exact identity `acc[27:11] + acc[10]`, using a signed 17-bit quotient; the discarded 

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 10:57:12] iter 002 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, narrow `sum3_0` to signed 24 bits, `sum3_1` to signed 28 bits, and `acc4` plus `acc4_next` to signed 28 bits, with explicit sign 

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 11:02:49] iter 003 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, express the rounded result as a signed 17-bit quotient using the exact `acc4[27:11] + acc4[10]` identity, then replace comparison

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-03 11:08:37] iter 004 | REJECT
- In `fir16_sym_core`, replace the eight 27-bit `prod1_*` registers with individually sized signed registers: 20 bits for C0, 22 for C1–C3, 24 for C4, 2

<!-- event:20ae74168c1b400f9802e3784c1976a876bb06158d6d7ac441cccf3754c8cfd1 -->
## [2026-11-03 11:14:16] iter 005 | REJECT
- Keep all `prod1_*` registers at 27 bits; do not repeat iteration 4’s product-register narrowing. Change `sum2_0`, `sum2_1`, `sum2_2`, and `sum2_3` to 

<!-- event:c7deaa336d0458919389c7ecb5e2694c83e32c916bac1ecca211b44f7069bdbe -->
## [2026-11-03 11:20:22] iter 006 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, replace the recursive `ready1 = !v1 || ready2` assignment with the equivalent direct expression `ready1 = !(v1 && v2 && v3 && v4 

<!-- event:dd4d352f8516f1af3b864f8170994e4a00422621a27cd7a6ba29315235589f42 -->
## [2026-11-03 11:26:04] iter 007 | REJECT
- In `fir16_sym_core`, replace the `always @(*)` saturation branches that compare `rounded[16:15]` against `2'b01` and `2'b10` with a check for `rounded

<!-- event:4f0e527a4c8dd395bd5eb85e8faec4199dd7db88eb1fbb8f363083daa2fa274d -->
## [2026-11-03 11:27:01] iter 008 | REJECT
- In `fir16_sym_core`, replace the `always @(*)` saturation branches that compare `rounded[16:15]` against `2'b01` and `2'b10` with a check for `rounded
