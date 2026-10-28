
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-26 10:02:52] iter 001 | ACCEPT [NEW BEST]
- Replace the top’s pass-through core instance with equivalent three-slot pipeline logic, preserving signed FIR results, valid/data hold behavior, synch

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-10-26 10:11:54] iter 002 | REJECT
- Keep the existing FIR datapath and three-slot registers, but replace `occupancy`, `occupancy_next`, and `full` bookkeeping with `r3 = !v3 || out_ready

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-10-26 10:15:30] iter 003 | REJECT
- Keep the occupancy/full readiness logic and all valid, data, history, reset, and pipeline registers unchanged. Change only the `fir_value` datapath: e
