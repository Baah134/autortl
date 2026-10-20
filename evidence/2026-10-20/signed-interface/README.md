# Signed and symbolic-interface live qualification

Four actual Vivado2025.2 xsim cases matched their expected verdicts, with no
model calls. Signed comparison uses mechanically generated signed ascending
ports, top wiring and testbench declarations. An independent golden function
explicitly interprets masked eight-bit two's-complement inputs; fixed opposite-
sign corner cases and deterministic traffic qualify the check. The unsigned
port mutant is rejected statically and also triggers real simulation assertions.

The symbolic-interface control is generated from a parsed stub retaining public
W/EXTRA parameters and its dependent local packed width. A testbench overrides
W=12, EXTRA=1 and checks thirteen-bit data with ascending/descending ports.
The control passes; the interface-identical stuck-zero mutant triggers assertions.
Compilation failures/timeouts do not count as qualification.

Executed from an uncommitted working tree over base1243e2e. harness_identity.json
records complete runtime file hashes; source/testbench hashes accompany each
result. The unchanged runtime was then published as the interface/storage
checkpoint. This is structural and finite simulation evidence, not a general
proof of parameterized behavior or physical signed datapath timing.
