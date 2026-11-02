
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-02 16:25:36] iter 001 | REJECT
- Inline the debouncer logic in `debouncer_top` and replace its binary counter with a 3-bit LFSR: use zero as the idle state, load a nonzero seed on the

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-02 16:28:01] iter 002 | REJECT
- In `debouncer_top`, keep the registered `clean` state and replace the LFSR state with a 3-bit down-counter: start the countdown on the first cycle `no

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 16:30:22] iter 003 | REJECT
- Replace the wrapper with equivalent logic inside `debouncer_top`, keeping the registered `clean` state and a 3-bit up-counter. Clear the counter when 

<!-- event:63ce19e07823e315e8501a7bcac7fc46b9310a5a9bcecf053b8f5995c10102c7 -->
## [2026-11-02 16:32:32] iter 004 | ACCEPT [NEW BEST]
- Replace the child instance in `debouncer_top` with inline logic that keeps a registered `clean` and a 3-bit Johnson counter, using the sequence `000, 
