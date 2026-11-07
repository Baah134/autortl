
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 09:11:24] iter 001 | REJECT
- In `axil_regbank`, replace the three repeated indexed `case` write branches for registers 0–2 with shared register-select and per-byte write-enable te

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 09:17:57] iter 002 | REJECT
- Replace the `case (araddr[4:2])` assignment to `rdata_reg` with bit-sliced selection: select bits `[7:0]` from all eight register words, and bits `[31

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-11-03 09:23:52] iter 003 | REJECT
- Change the `case (araddr[4:2])` read-data selection and the surrounding `araddr[5]` branch in `axil_rd_if` to use shared one-hot selects qualified by 
