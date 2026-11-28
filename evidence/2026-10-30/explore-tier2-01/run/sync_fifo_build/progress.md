
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-30 11:23:14] iter 001 | ACCEPT [NEW BEST]
- Replace the wrapper’s direct output path with a depth-3 shift-register FIFO: store accepted payloads in order, drive `out_data` from the registered he

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-10-30 11:26:13] iter 002 | REJECT
- Replace the seed’s `head`/`middle`/`tail` shift-register update cases with a three-slot circular buffer, explicit wrap for its read and write pointers
