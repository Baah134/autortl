
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-30 18:34:19] iter 001 | ACCEPT [NEW BEST]
- Replace the single eight-product expression feeding `sum_pipe0` with two registered 32-bit partial sums, each formed from four tap products using bala

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-10-30 18:49:22] iter 002 | ACCEPT [NEW BEST]
- Keep the existing `d[0:7]` delay line and pipeline registers, and add a parameter-conditional symmetric-coefficient path that pairs `d[0]+d[7]`, `d[1]

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-10-30 18:49:58] iter 003 | REJECT
- no candidate survived the ladder

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-10-30 18:50:36] iter 004 | REJECT
- no candidate survived the ladder

<!-- event:20ae74168c1b400f9802e3784c1976a876bb06158d6d7ac441cccf3754c8cfd1 -->
## [2026-10-30 18:51:19] iter 005 | REJECT
- no candidate survived the ladder

<!-- event:f76bb65dfcaad86c411534efe1897efc64533efa691c1a6a511acc5744161954 -->
## [2026-10-30 19:03:21] iter 006 | REJECT
- In the symmetric-coefficient generate branch, add a nested specialization for the exact default coefficient values (3, 7, 12, 18, 18, 12, 7, 3) that c
