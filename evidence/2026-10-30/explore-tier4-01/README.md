# Tier4 exploration 01: the first run of every tier4 entry

Exploratory, not a curriculum verdict: `tools/explore.py --tier 4 --jobs 2
--model gpt-6-luna` ran each entry through `run.py build` from its prose
request, without writing the curriculum history. Code: branch `claude/post-hold`
at 2d9b58c5 (timing progress, live companions, tier-concurrent history), run
from the `autortl-portability` worktree alongside the tier1-campaign-04 gate.
Budgets per entry: iterations from meta.yaml, best-of-1, 30 model calls, 40 tool
and 60 wall minutes. Every acceptance used the entry's independent, qualified
testbench (curriculum/tier4/qualify_tier4.py) as well as the generated oracle.

| Entry | Built from prose | Result (Basys 3, 100 MHz) | Iterations after build | Calls | Wall |
|---|---|---|---|---:|---:|
| crc16_stream_build | first try | **16 LUT, 34 FF, WNS +0.445 ns** | 3, all rejected (no LUT change) | 13 | 18.7 min |
| rr_regfile_build | first try | **41 LUT, 90 FF, WNS +0.554 ns** | 2, all rejected (no LUT change) | 10 | 15.2 min |
| spi_master_build | first try | **25 LUT, 36 FF, WNS +0.343 ns** | 3, all rejected (no LUT change) | 10 | 9.3 min |

## What the roles showed

- **Tier4 builds work from prose.** Each multi-module design (CRC-16 stream with
  valid/ready framing, round-robin arbiter feeding a read-first register file,
  SPI mode-0 master) passed its generated golden oracle and the independent
  testbench, and met timing on the first build.
- **Optimization never moved the objective.** Eight post-build candidates all
  verified, all met timing, and none changed the LUT count, so the evaluator
  rejected each one, correctly. One CRC candidate merged two 16-bit registers
  (34 → 18 FF) without changing LUTs; under `minimize_luts` that is not a gain.
- **The planner spent iterations on inlining.** Two of five CRC and arbiter
  proposals copied a frozen child's logic into the editable top unchanged.
  Vivado flattens the hierarchy, so the routed design is identical. Recorded
  as taxonomy `hierarchy_inlining_as_optimization`; the candidate boundary and
  the planner prompt now say inlining alone saves nothing.
- **The register file cannot use LUTRAM** because the contract resets all eight
  entries; the 64 storage flip-flops are required by the spec, not waste.

Per-entry role reports: `role-report-<entry>.md` (tools/role_report.py).
Simulator snapshots (xsim.dir) and Vivado scratch (.Xil) are not copied.
