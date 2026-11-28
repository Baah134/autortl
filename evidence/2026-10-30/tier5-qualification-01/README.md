# Tier5 testbench qualification 01

Each tier5 entry's independent testbench was run in Vivado 2025.2 xsim against
its reference design and ten realistic single-fault mutants
(`curriculum/tier5/qualify_tier5.py`, which reuses tier4's qualifier).
A testbench qualifies only when the reference prints TEST PASSED and every
mutant prints TEST FAILED with explicit FAIL lines and no watchdog.

| Entry | Reference | Mutants caught | Verdict |
|---|---|---|---|
| fir16_sym_build (16-tap symmetric FIR, valid/ready, 150 MHz target) | TEST PASSED | 10 / 10 | QUALIFIED |
| axil_regs_build (AXI4-Lite slave, 8 registers, W1C, SLVERR) | TEST PASSED | 10 / 10 | QUALIFIED |
| uart_rx_fifo_build (UART 8N1, 16x oversampling, FIFO, error counters) | TEST PASSED | 10 / 10 | QUALIFIED |

The testbenches and mutants were authored on branch `tier5-curriculum` and
checked only by reading and Python emulation before this run; this is their
first simulation. The first attempt compiled nothing because the qualifier
passed a relative output folder to xvlog, which runs inside each case folder;
fixed in `curriculum/tier4/qualify_tier4.py` (commit 6ac60682) before this run.

Files: `<entry>-qualification.json` (per-case verdicts, testbench and source
SHA-256) and `qualification-console.txt`.
