# Packet FIFO independent admission

The packet-tagged FIFO fixture passed admission before model generation.
The six selected configurations are (WIDTH,DEPTH)=(8,3),(1,1),(8,2),(8,4),
(13,5),(16,8); the first uses the mechanical top wrapper.

- Correct supervised control: all six configurations passed.
- Nineteen distinct source mutations: all detected by concrete behavioral
  assertions after compilation, with no infrastructure/watchdog kills.
  Capture/output truncation are overlapping observable faults, not independent
  semantic classes. Six mutations specifically target last-marker handling.
- Full Python regression: 1,105 passed in 288.12 seconds.
- Integrated fixture/driver focus: 60 passed in 5.09 seconds.

Real simulation used Vivado 2025.2 xvlog/xelab/xsim. Sources, testbench,
mutation manifests and raw simulator verdicts are retained below. The control
is qualification-only and never a generator seed. This proves the named
checks on the selected configurations; it is not all-parameter/formal proof,
generated-model success, routed PPA improvement or a held tier.

All 185 frozen source/test/fixture/guard identities matched at completion of
both jobs. source-verification.json records the subsequent documentation-only
README correction separately. Runtime and executable fixture/test identities
are unchanged. The generated grader's sideband sensitivity requires its own
measurement; a global stuck-zero mutant is insufficient evidence of that.
