
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-10-29 05:28:48] iter 001 | REJECT
- Replace the `case (sel)` assignment with a balanced mux expression: select between `a`/`b` using `sel[0]`, select between `c`/`d` using `sel[0]`, then
