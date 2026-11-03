
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-02 18:47:14] iter 001 | REJECT
- Keep the top interface and `// @latency 0` annotation, and replace the child instance with equivalent top-level state: registered `clean`, the prior `

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 18:49:25] iter 002 | ACCEPT [NEW BEST]
- Keep `// @latency 0` and inline the frozen child’s logic in `debouncer_top`, changing the counter’s saturated `stable_count != 3'd7` branch. On each u

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 18:51:44] iter 003 | REJECT
- Keep the top interface, `// @latency 0`, registered `clean`, and the existing synchronous active-high reset. Replace the current `stable_count + 3'd1`

<!-- event:63ce19e07823e315e8501a7bcac7fc46b9310a5a9bcecf053b8f5995c10102c7 -->
## [2026-11-02 18:54:04] iter 004 | ACCEPT [NEW BEST]
- Keep the top interface and `// @latency 0`, but replace `previous_noisy` tracking with a 3-bit consecutive-difference counter: clear it when `noisy ==
