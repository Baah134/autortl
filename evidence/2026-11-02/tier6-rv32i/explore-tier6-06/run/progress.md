
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 10:19:41] iter 001 | ACCEPT [NEW BEST]
- Change only `rv_regfile`: remove the reset loop that clears `x[1:31]`, retain the storage array, and add per-register valid bits that reset to zero an

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-02 10:37:36] iter 002 | REJECT
- In `rv_imem` and `rv_dmem`, remove the reset loops that clear the data arrays and add per-word valid bits that reset to zero; leave the wide arrays un
