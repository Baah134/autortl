
<!-- event:61a042fe144d80ee6306d17ce22db1d9ef2632f16e782e2dd64341c7fa9087fa -->
## [2026-11-02 18:29:07] iter 001 | REJECT
- In `mux4`, replace the `case (sel)` data selection with a combinational one-hot decode of all four `sel` values and an 8-bit bitwise-AND/OR masked sel
