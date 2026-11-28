# Pre-sign-off integrity check (November 2)

A full check of the repository before the final formal sign-off pass, on
`codex/contract-context` at 8abd6eb9 (after merging the tier 0-6 gate support).

| Check | Result |
|---|---|
| Git | Working tree clean apart from two placeholder archive scripts kept for the sign-off; every local branch, including all agent worktree branches, is merged into the checkout; no agent worktree holds uncommitted work |
| CI job 1: `pytest tests/` | **2,021 passed** |
| CI job 2: `pytest coordination hardware/basys3/harness_winners/tests hardware/basys3/fmax/tests tools/tests` | **237 passed** |
| Evidence audit: `tools/evidence_audit.py --rev HEAD` | **PASS** |
| Environment: `run.py doctor` (Vivado 2025.2, xvlog/xelab/xsim, Codex CLI logged in) | **ready** |
| Documentation: relative links in README, docs/, curriculum and hardware READMEs | 89 links in 45 files, **all resolve** |
| Board: archived all-harness UART echo bitstream reprogrammed on the Basys 3 (volatile JTAG), 20,000-byte stream | **20,000 / 20,000, 0 errors** |
| Testbench re-qualification in xsim (`requalify_all.py`): every curriculum entry with qualification material, each reference must pass and every planted fault must fail | **17 / 17 entries QUALIFIED, 234 simulations** |

Re-qualified entries: tier 2 packet FIFO (20 cases), skid buffer (9), sync
FIFO (14); tier 3 pipelined dot product (13), elastic dot product (19),
iterative divider (21), signed FIR (28), UART + FIFO (11); tier 4 CRC-16
stream, arbiter + register file, SPI master; tier 5 AXI4-Lite registers,
16-tap FIR, UART receiver + FIFO; tier 6 RV32I core, AES-128, CORDIC (11 each:
reference plus ten faults). Tier 2/3 entries were simulated from their
`qualification/cases.py` materialized folders; tier 3 UART + FIFO and tiers
4-6 through their own qualifiers.

Files: `requalification-summary.json` (per-case verdicts),
`requalification-console.txt`, `requalify_all.py` (the driver).
