
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 00:11:40] iter 001 | REJECT
- Replace the child instance with top-local `clean`, tracked-value, and 3-bit count state; on a changed sample, record `noisy` and set the count to repr

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-03 00:13:48] iter 002 | ACCEPT [NEW BEST]
- Replace the child instance with top-local `clean` state and a 3-bit saturating counter; do not add a tracked-value register. On synchronous active-hig

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 00:16:16] iter 003 | REJECT
- In `debouncer_top`, keep `clean_reg` and the 3-bit debounce state, but replace the binary increment and saturation checks with a zero-idle, nonzero LF

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-03 00:18:29] iter 004 | REJECT
- In `debouncer_top`, keep `clean_reg` and the 3-bit counter, but replace the binary up-counter and `count == 3'd7` saturation branch with a countdown: 
