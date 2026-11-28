
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-01 21:54:24] iter 001 | REJECT
- In `axil_rd_if`, change the `case (araddr[4:2])` that assigns `rdata_reg` on an accepted read into eight decoded select terms, each masking its corres

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-01 21:59:49] iter 002 | REJECT
- In `axil_rd_if`, replace the in-range `case (araddr[4:2])` assignments to `rdata_reg` with a variable indexed part-select of `regs_flat`, using `aradd

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-01 22:04:58] iter 003 | REJECT
- In `axil_regbank`, replace the nested `case (wr_idx)` and per-byte `if (wr_strb[b])` updates for `ctrl_reg`, `scratch_reg`, and `config_reg` with expl
