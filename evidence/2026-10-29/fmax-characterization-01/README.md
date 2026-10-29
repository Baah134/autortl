# How fast the six harness winners run, and what limits them

`hardware/basys3/fmax/fmax.py` searched for the fastest clock at which each
harness winner closes timing on the Basys 3's part, xc7a35tcpg236-1, in two
ways. An attempt counts as closed only when routed setup, hold and clock
pulse-width slack are all non-negative. Each winner's SHA-256 was checked
before use.

| Design | Harness flow Fmax | Its critical path | Out-of-context Fmax | Its critical path |
|---|---:|---|---:|---|
| Pipelined dot product | 107.5 MHz (9.30 ns) | register to output pad (OBUF) | 392.2 MHz (2.55 ns) | register to register, 6 levels (5 CARRY4, LUT2) |
| Elastic dot product | 101.5 MHz (9.85 ns) | register, LUT3, output pad | 384.6 MHz (2.60 ns) | register to register, 6 levels (5 CARRY4, LUT2) |
| Signed FIR | 103.1 MHz (9.70 ns) | register, LUT2, output pad | 181.8 MHz (5.50 ns) | register to register, 6 levels (4 CARRY4, LUT3, LUT4) |
| Iterative divider | 103.1 MHz (9.70 ns) | register, LUT2, output pad | 322.6 MHz (3.10 ns) | register to register, 5 levels (3 CARRY4, LUT2, LUT3) |
| Packet FIFO | does not close at 100 MHz in the default flow (−0.172 ns; see below) | register, LUT3, output pad | 425.5 MHz (2.35 ns) | register to register, 1 level (LUT5) |
| Sync FIFO | 101.0 MHz (9.90 ns) | register, LUT3, output pad | 384.6 MHz (2.60 ns) | register to register, 2 levels (LUT6, RAMD32) |

## What the two columns mean

**Harness flow** repeats the harness's own measurement, `SYNTH_TCL` in
`autortl/vivado.py`. The core is the top level, its ports get I/O buffers,
and external input and output delay is zero. The reproduction is exact. At
100 MHz, five of the six winners give the same routed WNS and WHS the
harness recorded, to the picosecond (`sweep/harness_slack_comparison.txt`).
The sixth, the packet FIFO, matches exactly once the harness's timing-doctor
options are applied (below).

**Out of context** synthesizes the core with `-mode out_of_context`: no I/O
buffers, the clock modeled from a global buffer, and only
register-to-register paths timed. That is the speed of the logic itself
inside a larger design.

## Findings

1. **The harness's timing objective measures pads, not logic.** Every
   harness-flow critical path ends at an output buffer. Each one is a
   register, at most one LUT, an `OBUF` and the pin, so all six top out
   between 101 and 107.5 MHz, whatever their logic does. The same cores run
   1.8× (FIR) and 3.1–3.8× (the others) faster out of context. So when the
   harness compares candidates on WNS at 100 MHz, it is mostly comparing
   pad and clock-insertion delay. That gap is recorded in `docs/TASKS.md`
   (`io_dominated_timing_metric`).
2. **Logic depth sets the out-of-context limits.** One step past its limit,
   every design fails on setup, by 16 to 93 ps, not on hold or pulse width.
   The FIR is the slowest at 181.8 MHz: a 6-level path through four CARRY4
   stages of its multiply-accumulate. Every other winner clears 320 MHz, and
   the FIFOs and dot products reach 385–425 MHz. The sync FIFO is close to a
   second limit as well. At 2.6 ns its pulse-width slack is only +0.050 ns,
   because its LUT-RAM storage has its own minimum pulse width. That is
   why the search checks pulse width as well as setup and hold.
3. **The packet FIFO closes 100 MHz only with the timing doctor's options.**
   The harness recorded +0.078 ns for this winner. That came from its
   `doctor_tool_knobs_trial`, which added `-retiming` to synthesis and
   `phys_opt_design` after placement. The default flow, which this sweep
   uses, misses by 0.172 ns on the same RTL. Rerunning with both options
   gives exactly +0.078 ns setup and +0.106 ns hold, the harness's numbers
   (`packet-fifo-with-doctor-options`). `-retiming` alone changes nothing.
   On the board this does not matter: the board build constrains its pins
   differently and met timing with +4.678 ns.

## Method notes

- Each attempt is a fresh in-memory project in one long-lived Vivado
  session: synthesis, opt, place, route.
- The search steers by setup slack inside a bracket that always shrinks,
  down to 0.05 ns.
- Timing-driven implementation is not monotonic near the edge. A reported
  Fmax is the fastest period that closed during the search, not a promise
  that every slower period closes.
- `sweep/ooc_limits.txt` gives, for each design, which check failed one step
  past its limit.
- `sweep/<design>/<mode>/search.json` lists every attempt.
  `p<period>/` holds its TCL, reports and Vivado console output.
- The sweep was paused twice, to free the Vivado queue for the UART
  harness runs. A paused search was discarded and run again from scratch,
  so every search here ran uninterrupted.
- `archive.py` built this folder, leaving out only Vivado `.Xil` scratch
  folders. `archive-manifest.json` hashes every file.
