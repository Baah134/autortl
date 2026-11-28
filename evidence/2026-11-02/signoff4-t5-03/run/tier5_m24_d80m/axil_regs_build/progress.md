
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 12:05:40] iter 001 | REJECT
- Change only `axil_rd_if`’s read-data selection: replace the `case (araddr[4:2])` over eight fixed `regs_flat` slices with a variable 32-bit part-selec

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 12:10:59] iter 002 | REJECT
- In `axil_wr_if`, replace the six-bit `aw_addr` register with a four-bit register for `awaddr[5:2]`, and update its reset, capture, range-check, and in

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 12:16:13] iter 003 | REJECT
- In `axil_regbank`, replace the separate `case (wr_idx)` branches and nested strobe checks for indices 0–2 with shared per-register select terms and pe
