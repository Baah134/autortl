# Harness-generated signed FIR on the Basys 3

Runs the signed FIR that AutoRTL generated and optimized (78 → 52 LUTs, timing
recovered) on a Digilent Basys 3, and checks every output against an
independent Python model.

| Path | Contents |
|---|---|
| `dut/signed_fir4.v` | The harness winner, byte-identical to `evidence/2026-10-26/generated-signed-fir4-attempt-01/run/signed_fir4_best.v`. Never edited by hand. |
| `rtl/basys3_fir4_shell.v` | Hand-written shell: UART in → input FIFO → FIR → output FIFO → 2-byte serializer → UART out. A UART break restarts the filter. |
| `constraints/` | Basys 3 pins from Digilent's master XDC |
| `sim/` | Self-checking testbench with a behavioral filter model |
| `scripts/` | `run_sim.ps1`, `build.tcl`, `program.tcl`, `fir_test.py` |

The UART receiver, transmitter and FIFO are shared from
[`../uart_echo`](../uart_echo/README.md).

Protocol: each byte is one signed 8-bit sample. Each output returns as a
sign-extended 16-bit little-endian value. The PC keeps at most 32 samples
outstanding (the input FIFO depth). LD0–LD7 show the last sample, LD14 latches
on a break and LD15 latches if a sample was ever lost.

## Verified results (October 28, 2026)

Full record: [evidence](../../../evidence/2026-10-28/basys3-fir4-01/README.md).

| Check | Result |
|---|---|
| Simulation | 256/256 outputs match, including a mid-stream restart |
| Fault checks | A wrong coefficient or a missing history reset makes the testbench fail |
| Implementation | 0 warnings; setup +2.718 ns, hold +0.113 ns; 160 LUTs in total, 49 in the FIR |
| Hardware | 100,000 random samples, 0 mismatches, 4 restarts |
| Negative control | A model with one wrong coefficient fails, with 4,965 of 5,000 differing |

## Run it

From this folder, with the board plugged in and switched on:

```powershell
$vivado = "C:\AMDDesignTools\2025.2\Vivado\bin"
New-Item -ItemType Directory -Force build | Out-Null
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_sim.ps1
& "$vivado\vivado.bat" -mode batch -nojournal -log build/vivado_build.log -source scripts/build.tcl
& "$vivado\vivado.bat" -mode batch -nojournal -log build/program.log -source scripts/program.tcl
python scripts/fir_test.py --samples 100000 --chunk 32
python scripts/fir_test.py --samples 5000 --wrong-model   # must FAIL
```

Programming loads the FPGA's SRAM only and is lost at power-off. Vivado use
follows the single-queue rule in `docs/AGENT_HANDOFF.md`.
