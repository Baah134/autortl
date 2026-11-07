# Independent UART sampling prompt review — November 7, 2026

Decision: approve the staged v2 proposal for coordinator integration after the
current frozen job is reconciled. No additional prompt or driver change is
needed. The canonical repository and the earlier proposal stage were not edited.

## Contract check

- `autortl/tbgen.py:229` drives a row on the falling edge. At latency zero it
  checks after `#1` without waiting for a rising edge; at latency one it waits
  for the next rising edge and then `#1`, observing nonblocking register updates.
- Latencies above one use `offset = latency - 1` and drain that many extra
  cycles. A logical row is checked after its Nth following rising edge. The
  proposed sentence about additional pipeline delay matches this convention.
- A clock port does not force latency one. A combinational output on a
  clock-bearing module can be sampled at zero; a FIFO's fall-through property
  alone does not establish the driver's observation phase. The v2 qualification
  is therefore appropriate.
- `generate_scoreboard_tb` samples accepted transfers before nonblocking
  assignments and checks output-transfer age from recorded input acceptance.
  Backpressure can delay an output transfer. It is a minimum accepted-transfer
  age, not the fixed-latency driver's post-edge observation phase.
- Fixed-latency shape validation requires every port to have protocol `none`.
  `_ports` includes every such output, and `_checks` compares every one on every
  selected row. An output named valid has no masking authority. Defining the
  empty/invalid data behavior is necessary under this existing schema; a
  deterministic hold-last policy is also possible when stated explicitly.
- No global conversion of latency zero to one, ban on clock-bearing zero-latency
  modules, invented output mask, or weakened acceptance check is introduced.

## Independent verification

Copied the prior proposal's 333 selected files into this review's `snapshot`
directory, including its new test. Ran the proposed tests together with existing
fixed-latency, scoreboard-latency, reset/driver, example and signed-corner tests:
**114 passed in 10.44 seconds**, exit zero. Exact command and input hashes are in
`receipt.json` and `inputs.json`; raw output is `tests.txt`.

The existing `test_tbgen_protocol.py` already covers latency three, and
`test_scoreboard_latency.py` covers zero, one and 1024. Adding duplicate tests for
those cases is unnecessary. The prior proposal stage's selected inputs remained
unchanged after this independent run. No model or vendor command was executed;
the board was not accessed.

These are prompt-delivery and Python/rendered-contract regressions. They do not
demonstrate improved LLM success or executed RTL behavior. The handwritten
pre/post-edge trace in the proposed tests is explanatory analysis; it must not
be described as simulator evidence.

## Simulator availability and safe next control

Read-only executable discovery found no `iverilog`, `vvp` or `verilator` on
PATH. This is not a claim that none exists anywhere on disk. `xvlog.bat`,
`xelab.bat` and `xsim.bat` resolve under
`C:/AMDDesignTools/2025.2/Vivado/bin`.

After the coordinator verifies the live queue, run only the three already
materialized sampling controls in separate fresh simulation directories. The
minimal tool sequence for each is:

1. `xvlog.bat <absolute RTL path> <absolute TB path>`
2. `xelab.bat accumulated_cell_tb -s sampling_control --debug off`
3. `xsim.bat sampling_control -runall`

Use the existing harness driver for timeout and exit recording if desired, with
only `xsim_run`; do not call a full synthesis/board suite. Every compile,
elaboration and simulation process must exit zero. Combinational latency zero
and clocked latency one must each report `TEST PASSED` and no assertion failure.
The same clocked RTL/oracle/stimulus at latency zero must report exactly the
three expected `FAIL index=1/2/3 signal=total` assertions and `TEST FAILED`.
Missing verdicts, watchdog expiration or tool errors do not establish a killed
behavioral negative control. Bind results to source, oracle, stimulus and TB
hashes before making any claim.

This sequence needs no Hardware Manager, hardware server, serial-port access,
device programming, bitstream generation or board reset. None of those actions
was performed during this review. The next control is simulator-only and remains
unexecuted by this worker.
