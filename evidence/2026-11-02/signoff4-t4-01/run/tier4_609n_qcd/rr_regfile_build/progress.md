
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-03 07:15:06] iter 001 | REJECT
- In `rr_arbiter4`, replace the `candidate`/`k` loop that indexes `req[candidate]` and the `case (winner)` address/data mux with explicit cyclic priorit

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-03 07:17:40] iter 002 | REJECT
- Change only `rr_arbiter4`’s winner selection and address/data mux: form mutually exclusive one-hot winner terms directly from `last` and `req` in roun
