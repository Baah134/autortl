
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-03 01:52:14] iter 001 | ACCEPT [NEW BEST]
- Keep the `d[0:7]` shift register, synchronous active-high reset, registered `y_out`, and `// @latency 1` unchanged. Replace the left-associated eight-

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 01:56:59] iter 002 | ACCEPT [NEW BEST]
- Keep the delay register, synchronous active-high reset, registered `y_out`, and `// @latency 1` unchanged. Add an elaboration-time fast path for `C0==

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-03 02:02:41] iter 003 | ACCEPT [NEW BEST]
- Keep `d[0:7]`, the synchronous active-high reset, registered `y_out`, and `// @latency 1` unchanged. Add a generate-time fast path for the exact defau

<!-- event:63ce19e07823e315e8501a7bcac7fc46b9310a5a9bcecf053b8f5995c10102c7 -->
## [2026-11-03 02:07:40] iter 004 | ACCEPT [NEW BEST]
- Change only the exact-default-coefficients generate branch: compress the shifted terms for `3*s0`, `7*s1`, `12*s2`, and `18*s3` with carry-save stages

<!-- event:20ae74168c1b400f9802e3784c1976a876bb06158d6d7ac441cccf3754c8cfd1 -->
## [2026-11-03 02:12:27] iter 005 | REJECT
- In the exact-default-coefficients specialization, change the 32-bit `acc` partial-sum registers and associated sum expressions to signed 23-bit values

<!-- event:f76bb65dfcaad86c411534efe1897efc64533efa691c1a6a511acc5744161954 -->
## [2026-11-03 02:17:10] iter 006 | REJECT
- Add an exact-default-coefficient generate branch that forms signed 17-bit sums `d[0]+d[7]`, `d[1]+d[6]`, `d[2]+d[5]`, and `d[3]+d[4]`, then applies we
