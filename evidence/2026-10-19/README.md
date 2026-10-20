# Retained evidence

`generated-testbenches/results.json` records nine real Vivado simulator checks.
All nine matched the expected result: valid combinational, latency1/latency3,
stateful and streaming circuits passed; wrong latency, a corrupted second
output, ignored backpressure and never-valid streaming circuits were rejected.
Each case includes its exact source/testbench hashes and raw tool logs.

`relocation-manifest.json` records the 317 file hashes verified across the move
from Documents to Downloads/autortl-work. It describes the files at move time;
subsequent source/Git changes are expected to differ. Existing Downloads/autortl
was not overwritten.

`prior-codex-counter-result.json` preserves the earlier generated 8-bit counter
trial. Its old `kind` label predates the replay correction; source_import metadata
identifies it as reverification without another model call. This design used
6 LUTs/8 FFs at a 10 ns clock. It is not a comparison with the 32-bit baseline.

`checkpoint-tests.txt` records the first published checkpoint: 411 tests passed.
`live-regression-tests.txt` records the subsequent repairs: 423 passed.
`live-tier0/` retains the unsuccessful first campaign and supervised repair
replays; read its README before interpreting those results. Tests
for full FSM recovery/build use controlled model/tool fixtures; the new full
build/optimization journal has not yet completed a successful live model-driven campaign.
Raw logs contain original absolute source paths because they preserve actual
tool output. Reproduction commands use the current checkout, not those old paths.
