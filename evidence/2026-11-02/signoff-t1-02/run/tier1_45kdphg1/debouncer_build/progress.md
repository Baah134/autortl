
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 15:57:33] iter 001 | ACCEPT [NEW BEST]
- Replace the child instantiation with top-level `clean_reg`, `candidate`, and 3-bit counter state; on a noisy change, capture the new candidate and cle

<!-- event:d42ec7c27d2155e42cf13b65059859c4a8c4206a8d590faa08a9985d755b7468 -->
## [2026-11-02 15:59:55] iter 002 | ACCEPT [NEW BEST]
- In `debouncer_top`, replace the `candidate`-based change detection with a saturating 3-bit counter that advances while `noisy != clean_reg` and clears

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-02 16:02:13] iter 003 | REJECT
- In `debouncer_top`, replace the saturating up-counter with a 3-bit down-counter: synchronously reset it to `3'b111`, reload it to `3'b111` whenever `n

<!-- event:2d0a32e8b9932981346c42c3a3b7c3464c8d137e938fcb61f6c4314c7c419044 -->
## [2026-11-02 16:03:11] iter 004 | REJECT
- In `debouncer_top`, replace the binary `count` increment/equality logic with a 3-bit Johnson sequence register that advances only while `noisy != clea
