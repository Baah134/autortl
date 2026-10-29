# Why the divider uses 30 FFs on the board and 38 in the harness

The harness measured its iterative-divider winner at 26 LUTs and 38 FFs
(`generated-divider-attempt-01/.../run_summary.json`). Built inside the Basys 3
test shell with its hierarchy kept, the same unedited file uses 26 LUTs and
30 FFs (`utilization_winner_in_shell.rpt`). This folder establishes why.

The winner was rebuilt standalone in a scratch directory with the harness's own
flow (`standalone.tcl`), copied from its `iter_003/cand_standard/synth.tcl`:

- the same part
- the same two input files
- `synth_design -flatten_hierarchy rebuilt`
- the same zero-delay I/O constraints
- `opt_design`, `place_design` and `route_design`

The result reproduces the harness's 38 Slice Registers exactly (`util.rpt`).
`flip_flops_standalone.txt` lists every flip-flop by name:

- **30 logical registers.** These are the RTL's 31 register bits (divisor 8,
  quotient 8, remainder 9, busy, out_valid, iteration 4) minus remainder bit 8,
  which drives nothing.
- **8 replicas: `quotient_work_reg[0..7]_lopt_replica`.** `standalone.log`
  shows `[Opt 31-389] Phase Sweep created 8 cells` during `opt_design`. As a
  top-level design, the quotient register drives both the output ports and
  internal logic, so Vivado duplicated it. Inside the shell the quotient never
  reaches a port, and no replicas are created.

So the difference is a consequence of the standalone top-level boundary, not
a different design or a measurement error. The same kind of boundary effect
explains the smaller differences of one or two LUTs or FFs for the FIR and
both FIFOs in `../basys3-harness-winners-01`. Those were not investigated
individually.
