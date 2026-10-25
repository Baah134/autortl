
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-25 16:18:59] iter 001 | ACCEPT [NEW BEST]
- Inline the frozen core’s two-slot logic in `elastic_dot4` and add a resettable `full` register that tracks `v1 && v2` after each edge; derive `in_read

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-10-25 16:24:46] iter 002 | ACCEPT [NEW BEST]
- Inline the core logic in `elastic_dot4` and apply Xilinx `use_dsp = "yes"` inference to each of the four 16-bit unsigned multiplication results; keep 
