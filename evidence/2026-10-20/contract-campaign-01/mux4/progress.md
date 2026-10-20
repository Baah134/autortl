
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-10-20 00:38:22] iter 001 | REJECT
- Replace the `case (sel)` assignment pattern with the explicit balanced selection `sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a)`. Keep the existing act
