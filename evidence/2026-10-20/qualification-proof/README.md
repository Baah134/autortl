# Qualification proof and duplicate-definition guards

**807 regression tests passed in 137.16 seconds.** Focused replay/build tests:
43 passed. Focused duplicate/compiler/triage tests:24 passed. Synthetic receipts
in unit tests are fixtures, not actual vendor invocations.

Stage snapshots now restore sim_log.txt and qualification.json; DONE identity
includes all raw simulation proof and qualification reports. Regression tests
delete original assertion proof, forge a missed probe and replay without new
simulator calls, then confirm original proof and misses return. Changing either
completed qualification report or negative proof invalidates DONE reuse.

The exact duplicate-module candidate from generated-streaming/build-golden-skid-03
now returns a DESIGN failure on VRFC10-3609 despite xvlog exit0. It stops before
xelab/xsim; the receipt and unchanged input hashes are retained here. Direct
synthesis also rejects Synth8-9873 (fixture-tested); unrelated warnings remain
accepted and nonzero infrastructure diagnostics retain precedence. No new
synthesis measurement or optimization gain is claimed by this regression.

The real regression uses the archived candidate skid_buffer.v plus its declared
frozen skid_buffer_core.v and the independent skid_buffer_tb.v. Invoke current
`autortl.vivado.xsim_run` with those ordered design files in a fresh directory;
expect failure_kind design, VRFC10-3609 and no xelab.log. Historical streaming
source is afcc080; the current guard source is identified by its Git commit and
the following fresh campaign runtime manifest. The first local helper invocation
omitted RunConfig.mode and stopped before tool launch; correcting its argument
produced the retained real compiler verdict.

Archives omit compiled vendor trees and journal artifact copies. Retained
absolute paths are original provenance; archives are not resumable directories.
