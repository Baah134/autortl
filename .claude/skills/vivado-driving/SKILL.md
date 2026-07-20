---
name: vivado-driving
description: "Use when writing or debugging the toolchain layer: driving Vivado in batch mode, xvlog/xelab/xsim fast paths, TCL path rules, report generation, and Windows-specific quirks."
---
# Driving Vivado (battle-tested knowledge from AutoRTL v1-v3)

## Paths (Windows)
- TCL requires forward slashes. Convert every path: `C:/Users/...`, never `C:\Users\...`. Backslash paths break tclargs silently.
- Always pass ABSOLUTE paths to TCL scripts.
- Reject any path containing quotes, braces, `$`, or `;` before it reaches TCL (injection boundary).

## The fast path (skip project creation)
Project mode (`create_project`) costs 30-60s and CACHES COMPILED SOURCES — stale caches caused false failures for us. Batch flow is faster and stateless:
1. `xvlog design.v tb.v` (compile, seconds)
2. `xelab tb_top -s snap --debug off` (elaborate)
3. `xsim snap -runall` (run)
If a project flow is ever used, `file delete -force` the project dir first.

## Synthesis in batch
Non-project mode: `read_verilog` + `synth_design -top X` + `opt/place/route` + reports. Write the XDC from TCL itself so the clock constraint always exists.

## Message severity
`set_msg_config -id {Synth 8-327} -new_severity ERROR` promotes dangerous warnings. Promote only; never demote or suppress.

## Reports worth parsing
- `report_utilization` (post-route version is truth)
- `report_timing_summary` (WNS/WHS)
- `report_design_analysis -logic_level_distribution` (logic levels for the Timing Doctor)
- `report_power`

## Known infra failure signatures (retry, don't blame the design)
- file locks on .wdb/.pb (xsim holds handles after a run)
- license hiccups; `Connection refused/reset`
- `vivado.bat not recognized` (PATH)
- timeouts
