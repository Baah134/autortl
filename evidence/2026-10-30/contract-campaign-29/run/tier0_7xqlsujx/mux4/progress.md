
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-10-30 11:03:18] iter 001 | REJECT
- Replace the `case (sel)` data selection with an explicit balanced 2:1 mux tree, first selecting between `a`/`b` and `c`/`d` using `sel[0]`, then selec
