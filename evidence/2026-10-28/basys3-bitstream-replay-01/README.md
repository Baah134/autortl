# Board replay from the archived bitstreams

This run checks the bitstream archive from the board side. Each of the six
harness winners was programmed onto the Basys 3 straight from
`../basys3-bitstreams-01/harness_winners/<design>.bit`, not from a build
folder. Then the same hardware checks as the original run were repeated.
Nothing was synthesized. `replay_all.py` is the exact script, which uses the
board suite's `--bit` option. The board was on UART COM10 at 115200 baud.

| Design | Hardware vs. model | Wrong model | Payload = tested payload |
|---|---|---|---|
| fir4 | 50,000/50,000, 0 mismatches, 10 restarts | rejected: 1,990/2,000 differ | yes |
| elastic_dot4 | 50,000/50,000, 0 mismatches, 10 restarts | rejected: 1,983/2,000 differ | yes |
| dot4_pipeline | 50,000/50,000, 0 mismatches, 10 restarts | rejected: 1,983/2,000 differ | yes |
| iterative_divider | 50,000/50,000, 0 mismatches, 10 restarts | rejected: 2,000/2,000 differ | yes |
| packet_fifo | 50,000/50,000, 0 mismatches, 10 restarts | rejected: 2,000/2,000 differ | yes |
| sync_fifo | 50,000/50,000, 0 mismatches, 10 restarts | rejected: 2,000/2,000 differ | yes |

Each `model_50000.json` records the configuration payload digest of the file
that was programmed. All six equal the tested payloads in
`basys3-harness-winners-01/summary.json`, so this replay ran the same images
as the original results. The stimulus seed is fixed, and the wrong-model
mismatch counts match the original run exactly. The board's behaviour
reproduced bit for bit.

`exit_codes.json` holds the exit code of every program and check (all 0:
programming succeeded, the model checks passed, and the wrong-model checks
failed as required). Each design folder keeps the programming console and
both hardware reports.
