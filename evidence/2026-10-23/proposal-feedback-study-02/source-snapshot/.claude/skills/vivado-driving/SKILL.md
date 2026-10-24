---
name: vivado-driving
description: "Contract-preserving vivado-driving guidance for AutoRTL."
---
# Driving Vivado

Use harness-owned non-project batch templates and sanitized absolute forward-slash
paths. Model text must not become Tcl, shell commands or paths. Preserve the fixed
contract, clocks, reset and cycle latency; never relax constraints to make a pass.
Use unique run directories and recorded source hashes to prevent stale artifacts.
Do not delete a project or shared directory as an automatic cache workaround.

Compile/elaborate/simulate using configured xvlog/xelab/xsim executables; preserve
all logs and require the independent TB verdict. Synthesize/place/route with the
configured device and clock/I/O assumptions. Parse post-route utilization, setup
WNS and hold WHS; retain actual timing, utilization and power reports.
Promote dangerous diagnostics; never demote/suppress them. Missing reports are
unknown/failing evidence, never zero-resource successes. Tool versions and option
support come from actual execution, not guessed defaults.
Infrastructure retries are bounded and preserve RTL. Record unavailable binaries,
locks, licenses and timeouts separately from design failures. Physical hold repair
uses harness-controlled tool options, not RTL delay chains or extra cycles.
