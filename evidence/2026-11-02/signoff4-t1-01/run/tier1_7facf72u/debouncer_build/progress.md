
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-02 23:27:41] iter 001 | REJECT
- Replace the child instance with equivalent sequential logic inside `debouncer_top`, retaining the `clean_reg` and `candidate` state and the synchronou

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-02 23:32:40] iter 002 | REJECT
- Inline the frozen child’s logic into `debouncer_top` and complement the counter encoding: reset the counter to `3'd7`, treat that state as the initial

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-02 23:37:41] iter 003 | ACCEPT [NEW BEST]
- In `debouncer_top`, replace the child instance with a 7-bit history register and registered `clean`; synchronously clear both on active-high `rst`, sh

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-02 23:40:39] iter 004 | REJECT
- In `debouncer_top`, keep the seven-bit shift history and registered `clean_reg`, but store `~noisy` in the history and reset history to `7'b1111111`. 
