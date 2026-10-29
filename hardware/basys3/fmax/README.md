# How fast do the harness winners run?

The harness optimizes each design at a 100 MHz target on the Basys 3's part,
xc7a35tcpg236-1. This tool asks the follow-up question an FPGA engineer would:
how much faster could each winner be clocked, and what limits it? It
measures every winner two ways:

| Mode | What it times | Why |
|---|---|---|
| `harness` | The core as the top level, with I/O buffers on its ports and zero external input and output delay. This is the same constraint set as the harness (`autortl/vivado.py`, `SYNTH_TCL`). | This is what the harness actually optimized against. |
| `ooc` | The core synthesized out of context: no I/O buffers, the clock modeled from a global buffer, only register-to-register paths. | This is the speed the logic can reach inside a larger design. |

## Method

`fmax.py` runs one fresh in-memory Vivado project per attempt: synthesis,
opt, place, route at one clock period, all in a single long-lived Vivado
session. An attempt **closes** only when routed setup, hold and clock
pulse-width slack are all non-negative with no failing endpoints.

The pulse-width check matters. At 2 ns the clock itself breaks the device's
minimum pulse width, even where setup might pass.

The search starts at 10 ns (100 MHz), which must close. Each later period is
predicted from the last attempt's setup slack, and a bracket between the
fastest closing and slowest failing periods guarantees termination. It stops
when the bracket is 0.05 ns wide, usually after 3 or 4 attempts.

Timing-driven implementation is not monotonic near the edge. The reported
Fmax is the fastest period that closed during the search, not a guarantee
that every slower period closes. Each winner is checked against its
recorded SHA-256 before it is used.

```
python hardware/basys3/fmax/fmax.py run --out <dir> [--design NAME] [--mode ooc|harness]
python hardware/basys3/fmax/fmax.py summarize <dir>
python -m pytest hardware/basys3/fmax/tests -q        # no Vivado needed
```

The full sweep of all six winners is in progress. So far, the signed FIR's
logic closes at **181.8 MHz out of context**, while its harness-flow slack
at 100 MHz is only +0.169 ns, set by an output pad. Results and every
attempt's reports will be archived in
`evidence/2026-10-29/fmax-characterization-01` when the sweep finishes.
