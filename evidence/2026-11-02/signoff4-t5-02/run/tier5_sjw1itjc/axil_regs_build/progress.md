
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 10:41:36] iter 001 | REJECT
- In `axil_wr_if`, replace the six-bit `aw_addr` state with a four-bit register containing `{awaddr[5], awaddr[4:2]}` when the AW handshake occurs, and 

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 10:47:06] iter 002 | REJECT
- In `axil_wr_if`, keep synchronous reset on `aw_full`, `w_full`, `b_valid`, and `b_resp`, but move `aw_addr`, `w_data`, and `w_strb` capture into separ

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 10:52:32] iter 003 | REJECT
- In `axil_rd_if`, replace `regs_flat[{araddr[4:2], 5'b0} +: 32]` with an explicit case on `araddr[4:2]` selecting the corresponding 32-bit slice, retai
