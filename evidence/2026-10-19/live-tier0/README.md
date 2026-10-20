# First bounded live tier0 campaign

`campaign-01/summary.json`: 0/2 passed, no tier held. The runtime corresponds
to the code in 8d5eb09; runtime.json retains implementation hashes. Each entry
had one iteration/candidate, at most eight model calls, twelve Vivado minutes,
eighteen wall minutes and one infrastructure retry.

- Counter: the original 32-bit baseline passed simulation and routing: 54 LUTs,
  37 FFs, WNS 5.491 ns under the original clock-only constraints. Contract
  reviews repeatedly rejected proposals. The old loop still generated from an
  unreviewed final revision. Its candidate omitted a timescale, hit XSIM 43-4099,
  and exhausted the eight model calls before repair. No candidate was accepted.
- Mux4: simulation and routing completed, but timing slacks were absent because
  clock-only constraints did not time its boundary paths. The metric gate
  rejected this evidence; no model call or design repair was attempted.

The implementation now stops rejected negotiation, records explicit budget
outcomes, prepares generated RTL with a default timescale and constrains I/O
paths. Default boundary timing assumes an ideal synchronous external device:
zero minimum/maximum input/output delay relative to clk. It is an experiment
assumption, not a board timing specification. No message severity was reduced;
missing timing remains a failure. New constraints require fresh baselines.

Each campaign archive-manifest.json lists original bytes of retained sources,
constraints, reports, model-stage results, configuration, budgets and event logs.
Simulator binaries, Vivado caches and duplicated journal artifacts are omitted.
This is an evidence archive, not a relocatable resumable experiment directory.

The separate supervised repair replay uses no model calls. Its results and raw
logs are retained alongside this campaign. It does not count as a successful
autonomous optimization campaign or a qualifying curriculum run.

## Repair results

- live_repairs_01: counter simulation passed; mux timing remained absent.
  Vendor diagnostic Designutils 20-1307 showed that XDC ignores Tcl `if`.
- live_repairs_02: stopped by the coordinator after verifying its exact owned
  launcher command, because its script still used unsupported XDC control flow.
  This was an operator cancellation, not a design failure or successful test.
- live_repairs_03: counter simulation passed; mux simulation and routed timing
  passed with supported Tcl boundary constraints: 8 LUTs, 8 FFs, WNS 0.579 ns,
  WHS 0.052 ns at 10 ns on xc7a35tcpg236-1. Both input and output missing-delay
  counts are zero. The synthesized hold violations were repaired during routing.
- Final full suite: 423 passed in 62.33 seconds. The retained invalidated test
  attempt overlapped an implementation edit and its resume drift guard refused
  the changed runtime. The final suite ran against unchanged implementation.

validation-command.py preserves the supervised replay command. Its source
input refers to the original local campaign directory; that source is also
archived in campaign-01/counter/iter_001/cand_standard/counter.v. Archives omit
simulator binaries and cannot themselves be passed directly to `resume`.
