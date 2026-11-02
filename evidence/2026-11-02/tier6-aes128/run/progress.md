
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 11:05:40] iter 001 | ACCEPT [NEW BEST]
- In `aes_round`, replace the `gf_mul` based exponentiation inside `aes_sbox` with a complete 256-entry case lookup matching the existing `aes_key_step`

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 11:09:39] iter 002 | ACCEPT [NEW BEST]
- In `aes_round`, replace the current `mix_column` equations with the equivalent shared-total form: compute `t = a0 ^ a1 ^ a2 ^ a3`, then each output by

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 11:13:45] iter 003 | REJECT
- In `aes_round`, replace the `mixed_state = shifted_state` plus `if (!final_round)` whole-column selection with the shared-total correction form: each 

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-02 11:19:12] iter 004 | REJECT
- In `aes_sbox_lookup`, replace the flat 256-entry `case(value)` with a two-level 4-bit decomposition: use `value[7:4]` to select a bank and `value[3:0]
