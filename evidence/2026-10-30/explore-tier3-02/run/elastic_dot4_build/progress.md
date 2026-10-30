
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-10-30 18:13:45] iter 001 | ACCEPT [NEW BEST]
- Replace the child instance with equivalent top-level logic and apply Vivado’s `use_dsp = "yes"` directive to the four unsigned 8×8 product expressions

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-10-30 18:21:42] iter 002 | REJECT
- Replace the four separately declared product wires and the separate `input_sum01` / `input_sum23` additions with two explicitly 17-bit unsigned pair s

<!-- event:79d3316934e8191be36823a91635bdbf27a385745101937127e4aa8adf83f875 -->
## [2026-10-30 18:35:24] iter 003 | REJECT
- In the editable top’s elastic pipeline, replace `stage1_sum01` and `stage1_sum23` with one 18-bit stage-one result register, computed from all four ex
