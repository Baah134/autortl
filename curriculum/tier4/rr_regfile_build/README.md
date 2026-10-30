# Round-robin arbiter feeding a register file (tier 4)

`rr_regfile` mechanically wires two generated children:

| Child | Inputs | Registered outputs |
|---|---|---|
| `rr_arbiter4` | `req[3:0]`, `addrN[2:0]`, `dataN[7:0]` for N=0..3 | `grant[3:0]` (external), `wr_en`, `wr_addr[2:0]`, `wr_data[7:0]` |
| `regfile8x8` | `wr_en`, `wr_addr`, `wr_data` (from the arbiter), `rd_addr[2:0]` | `rd_data[7:0]` (external) |

The three write-port signals are explicit `connections`; they are not top-level
ports. Both children are fixed-latency, latency 1, synchronous active-high reset.
No aggregate top latency is annotated (the mechanical wrapper only inherits
latency through a single transparent child).

## Contract

The arbiter remembers the last winner (reset value 3, so requester 0 wins first)
and at each edge grants the first requester after it, cyclically; it registers a
one-hot `grant` and the winner's address/data with `wr_en=1`, or all zeros when
nothing is requested. The register file is read-first: `rd_data` takes the old
contents of `rd_addr`, then the registered write lands. Reset clears the pointer,
all outputs and all eight entries.

Integrated timing: a request sampled at edge k is registered by the arbiter
after k, written at edge k+1, and visible to a read sampled at edge k+2. A read
of the same address sampled at k+1 returns the old value.

## What it stresses

- Multi-module decomposition with an internal bus that the top never exposes,
  so integration faults show up only through `rd_data`.
- Two generated cycle-level golden oracles (fixed-latency path for both
  children), plus a supplied integration testbench as the top authority.
- Fairness state and same-edge read/write ordering, both classic sources of
  plausible-but-wrong RTL.
- Optimization of the mechanical top with frozen children; the mutant set
  includes one top wiring fault.

## Independent testbench

`rr_regfile_tb.v` models the pointer, the registered write port, the eight
entries and the registered read itself, and checks `grant` and `rd_data` after
every edge and again after the next input change (outputs must hold between
edges). It covers full rotation, all sixteen request patterns, lone requesters,
repeated same-address write/read collisions, an entry that must survive idle
cycles with noisy write inputs, a reset with every entry nonzero and a write
pending, two off-edge reset pulses with nonzero state, 1500 seeded random cycles
(xorshift32) with two resets, and a final read-back of every entry. It reads no
DUT internals and its schedule never depends on DUT outputs.

## Qualification (not yet run)

`qualification/reference.v` contains both children and the mechanical top
(byte-identical to `top_verilog(spec)`); `qualification/mutants.json` has ten
single-site faults across the arbiter, the register file and the top wiring.

```powershell
python curriculum/tier4/qualify_tier4.py curriculum/tier4/rr_regfile_build runs/tier4-qual/rr_regfile
```

No simulation of this fixture has been performed; nothing here is evidence of
compilation, mutant detection or PPA.
