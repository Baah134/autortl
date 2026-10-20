# FIFO reference qualification

Six actual Vivado 2025.2 xsim cases matched expected verdicts. Repaired reference
passes AW=2 and AW=4, DW=8; corrupted read-data and inverted full-comparator mutants
trigger explicit testbench assertions at both depths. No compile failure or
infrastructure timeout counts as mutation detection. Model calls: 0.

The independent transaction queue checks capacity, changing blocked writes,
empty/disabled read hold,8 fill/drain rounds, 800 deterministic random write-clock
cycles, final drain and coordinated reset/retest. Clock periods 10/14 ns with a 0.5 ns
phase offset avoid shared-queue coincident edges. All checks are bounded.

Only digital transaction behavior at these configurations is established.
No unilateral reset contract, metastability reliability, CDC constraint closure,
placement or routing claim. FIFO reference is separate from the singleclock
physical optimization curriculum. Exact source/TB hashes and raw logs retained.
The archived local driver takes checkout path, uses installed Windows Vivado binaries
and refuses to overwrite logs/fifo-reference-01.
