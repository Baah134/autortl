# Basys 3 bitstreams that were tested on the board

These are the exact bitstreams behind the board results of 2026-10-28, copied
unchanged from the build folders that produced them. With a Basys 3 you can
program one and rerun its board test without Vivado synthesis.

| File | Board result | Recorded in |
|---|---|---|
| `basys3_uart_echo_v02.bit` | UART echo, 1,000,000 bytes with 0 lost | `basys3-uart-echo-02/manifest.json` |
| `basys3_fir4_shell.bit` | FIR01 winner behind its UART shell, 100,000/100,000 | `basys3-fir4-01/manifest.json` |
| `harness_winners/<design>.bit` | Each of the six harness winners, 50,000/50,000 | `basys3-harness-winners-01/summary.json` |

`make_manifest.py` wrote `manifest.json` and refuses to write it unless every
file's SHA-256 equals the digest its board evidence recorded. For the six
harness winners it also checks the configuration payload: the bitstream with
its build-time header removed. That payload is what the board actually
loads, and it must equal the payload that was programmed and tested. The
header differs between builds because it records the build time. These
harness-winner files come from the rebuild with `keep_hierarchy`, whose
payloads are identical to the tested ones (see
`basys3-harness-winners-01/README.md`).

The superseded v01 UART echo bitstream is not here. The v02 build
overwrote it in the same build folder before bitstreams were archived, and
`tools/evidence_exceptions.json` records that loss. Its source is
kept in `basys3-uart-echo-01/source-snapshot`.

## Reprogramming the board

For a harness winner, from `hardware/basys3/harness_winners/`:

```
python -m hwsuite program --design <name> --bit ../../../evidence/2026-10-28/basys3-bitstreams-01/harness_winners/<name>.bit
python -m hwsuite hw --design <name> --bit ../../../evidence/2026-10-28/basys3-bitstreams-01/harness_winners/<name>.bit --count 50000
```

The other two load with the same `program.tcl`
(`vivado -mode batch -source hardware/basys3/harness_winners/scripts/program.tcl -tclargs <file>`)
and are tested with `echo_test.py` and `fir_test.py` in their own folders.
`../basys3-bitstream-replay-01` did exactly this for all six harness winners.

In CI, `tools/evidence_audit.py` checks every file here against
`manifest.json`, and checks that the bitstream digests in the UART echo and
FIR board manifests resolve to these files. A board-suite test,
`test_archived_bitstreams_match_the_board_evidence`, checks the six harness
winners' file and payload digests against `basys3-harness-winners-01/summary.json`.
