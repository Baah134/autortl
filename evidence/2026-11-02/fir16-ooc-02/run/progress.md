
<!-- event:b506afc0511c9f12af719b004a257eaa4339ef00b7d9330ea28ddf1ef03efdb7 -->
## [2026-11-02 09:56:02] iter 001 | ACCEPT [NEW BEST]
- Keep the history update and ready/valid behavior unchanged, but replace the full combinational FIR result feeding `d1` with arithmetic payloads carrie

<!-- event:2ebc0c784024f78c800ae6d9e883eaf8d1ef64ada2b438c593b11e8668011d22 -->
## [2026-11-02 10:07:53] iter 002 | REJECT
- Keep the top interface, `// @latency 5`, history update, and ready/valid logic unchanged. Replace the stage-2 all-eight-product accumulation with two 

<!-- event:a8c8c027131044d657e8acc6a3c226aa901f204dd870a44c1cd4c1250c70d21a -->
## [2026-11-02 10:20:44] iter 003 | ACCEPT [NEW BEST]
- Keep `pair1` and the ready/valid chain unchanged, but replace `acc2 <= total_acc` with eight signed 27-bit product registers for `p0` through `p7`, ca

<!-- event:63ce19e07823e315e8501a7bcac7fc46b9310a5a9bcecf053b8f5995c10102c7 -->
## [2026-11-02 10:27:30] iter 004 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, replace the single `acc3 <= total_acc` operation with two signed 28-bit stage-3 registers: one for `p0_reg` through `p3_reg`, and

<!-- event:76cad1b1a61611b20401ea55df715d8708bc989248b0431ee19b5a282dc27bbd -->
## [2026-11-02 10:32:55] iter 005 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, change `rounded4` and `rounded_value` from signed 28-bit registers/wires to signed 17-bit values; the contract’s accumulator boun

<!-- event:c7deaa336d0458919389c7ecb5e2694c83e32c916bac1ecca211b44f7069bdbe -->
## [2026-11-02 10:39:26] iter 006 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, change only the `result5` saturation logic: detect signed 17-bit overflow with `rounded4[16] != rounded4[15]`, select positive or

<!-- event:dd4d352f8516f1af3b864f8170994e4a00422621a27cd7a6ba29315235589f42 -->
## [2026-11-02 10:44:22] iter 007 | REJECT
- In `fir16_sym_core`, replace the eight 27-bit product registers with signed widths sized for each coefficient’s full 17-bit pair-sum range: 20, 22, 22

<!-- event:4f0e527a4c8dd395bd5eb85e8faec4199dd7db88eb1fbb8f363083daa2fa274d -->
## [2026-11-02 10:49:25] iter 008 | REJECT
- In `fir16_sym_core`, change `acc3_lo` storage to signed `[23:0]`; the `p0` through `p3` coefficient magnitudes sum to 68, so the partial accumulator’s

<!-- event:af78fe9612b009e6cbc21759fe0e5e50d3f3ce8576c23ba4eccf76469e19b8b9 -->
## [2026-11-02 10:53:48] iter 009 | ACCEPT [NEW BEST]
- In `fir16_sym_core`, replace the 17-bit `rounded4` payload with a 16-bit stage-4 register holding the rounded and saturated result, and remove the sta

<!-- event:f00821f7603647b1922bd15d93c4cd4a988176c2c9da863e65abf062219d4e00 -->
## [2026-11-02 10:59:21] iter 010 | REJECT
- In `fir16_sym_core`, replace the eight full-scale coefficients with their halves (`-3, -10, -12, 9, 55, 113, 165, 195`), store each product in a signe
