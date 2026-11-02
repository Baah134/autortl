
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-02 15:28:52] iter 001 | REJECT
- Replace the transparent `debouncer` instance with equivalent top-level sequential logic, retaining `clean`, the sampled input, and the three-bit stabi

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 15:31:13] iter 002 | ACCEPT [NEW BEST]
- In `debouncer_top`, replace the transparent child instance with top-level sequential logic and retain the required `// @latency 0` annotation. Remove 

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 15:33:25] iter 003 | REJECT
- In `debouncer_top`, replace the separate `stability_count == 3'd7` update-and-clear branch with a 4-bit temporary sum of the 3-bit count plus one; whi

<!-- event:63ce19e07823e315e8501a7bcac7fc46b9310a5a9bcecf053b8f5995c10102c7 -->
## [2026-11-02 15:35:44] iter 004 | ACCEPT [NEW BEST]
- Keep `clean_reg` as the registered output and replace the binary `stability_count` progression with a 3-bit LFSR: use `000` as the matching/idle state
