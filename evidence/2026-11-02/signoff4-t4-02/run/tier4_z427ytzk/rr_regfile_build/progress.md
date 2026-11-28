
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 07:44:15] iter 001 | REJECT
- Remove `wr_en_reg` and drive `wr_en` combinationally as the reduction OR of `grant_reg`. Keep `grant_reg`’s reset, winner, and idle updates unchanged,

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 07:46:41] iter 002 | REJECT
- In `rr_arbiter4`, derive a one-hot winner mask from `last` and `req`, preserving the specified cyclic priority, then register that mask directly as `g
