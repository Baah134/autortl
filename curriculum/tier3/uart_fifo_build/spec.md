Build a UART transmitter fed by a synchronous byte FIFO. Bytes arrive on a
valid/ready input stream, wait in the FIFO, and leave one at a time as 8N1
serial frames on `tx`. An independent testbench checks the top ports cycle by
cycle, so everything below is exact; any design that meets it is observably
identical at the top ports.

## Top module `uart_fifo` (exact name, no parameters)

| Port | Direction | Width | Meaning |
|---|---|---|---|
| `clk` | input | 1 | single clock; every register updates on its rising edge |
| `rst` | input | 1 | synchronous, active-high reset |
| `in_data` | input | 8 | byte to send, sampled only at an accepting edge |
| `in_valid` | input | 1 | `in_data` is offered |
| `in_ready` | output | 1 | the design accepts a byte at the next rising edge if `in_valid` is high |
| `tx` | output | 1 | serial line; idle high |

No other top ports. Fixed timing values at the top: one bit lasts
CLKS_PER_BIT = 16 clk cycles (a frame is 160 cycles), and the FIFO holds up to
DEPTH = 8 waiting bytes.

## Required child `uart_tx` (exact name, parameter and ports)

The testbench also instantiates this child directly with other bit periods, so
its interface is fixed: `module uart_tx #(parameter CLKS_PER_BIT = 16)` with
ports `clk` (input 1), `rst` (input 1), `tx_data` (input 8), `tx_valid`
(input 1), `tx_ready` (output 1), `tx` (output 1). It must honor
CLKS_PER_BIT for every value from 2 to 255, not only the default: size its
counters from the parameter and never hard-code 16 (the testbench checks 2, 3
and 7 directly and 16 through the top). The top instantiates it with
CLKS_PER_BIT = 16.

`uart_tx` contract, with P = CLKS_PER_BIT and frame length F = 10*P:
- A byte is accepted at a rising edge s when `tx_valid` and `tx_ready` are both
  high and `rst` is low. The frame of that byte starts at edge s.
- After edge s+j, for j = 0 .. F-1, `tx` is bit floor(j/P) of the frame:
  bit 0 is the start bit (0), bits 1..8 are `tx_data[0]` .. `tx_data[7]`
  (least significant bit first, as sampled at edge s), bit 9 is the stop bit (1).
- `tx_ready` is high when no frame is in progress, and also during the last
  clk cycle of the stop bit (after edge s+F-1, before edge s+F); low otherwise.
  So a byte offered then is accepted at edge s+F and its start bit follows the
  previous stop bit with no idle cycle. If no byte is accepted at edge s+F the
  line idles at 1.
- `tx_ready` and `tx` depend only on registered state (never combinationally on
  any input), so they change only just after rising clk edges.
- Reset: at a rising edge with `rst` high, any frame in progress is abandoned
  and nothing is accepted; after that edge `tx` = 1 and `tx_ready` = 1. A
  reset pulse that spans no rising edge has no effect.

## Top contract (`uart_fifo`)

Let "waiting" be the number of accepted bytes whose frame has not started yet
(the byte currently being sent is not waiting and does not occupy a FIFO slot).
- `in_ready` is high exactly when waiting < 8, computed from registered state
  only (not from `in_valid`, `in_data` or `rst`); it is high during and after
  reset.
- A byte is accepted at a rising edge k when `in_valid` and `in_ready` are high
  and `rst` is low; `in_data` is sampled at that edge. The source may raise or
  drop `in_valid` and change `in_data` at any time; nothing else is sampled.
- A frame starts at rising edge s (rst low) when at least one byte accepted
  before edge s is waiting and either no frame is in progress or the current
  frame, started at edge s', ends at s = s'+160. The oldest waiting byte is sent, in
  acceptance order, using exactly the `uart_tx` frame timing above with P = 16.
  The start and an acceptance may happen at the same edge.
- Consequences: a byte accepted at edge k into an empty, idle design starts its
  frame at edge k+1, so `tx` falls just after edge k+1; while bytes are
  waiting, frames are back to back with no idle cycle; with 8 bytes waiting
  `in_ready` is low until the next frame start, and is high again just after it.
- Reset at a rising edge with `rst` high discards every waiting byte, abandons
  the current frame and accepts nothing; afterwards `tx` = 1, `in_ready` = 1 and
  nothing is sent until new bytes are accepted. A reset pulse that spans no
  rising edge has no effect.

## Decomposition

Use at least two generated modules, a synchronous FIFO and `uart_tx`, plus the
mechanical top (the harness wires the top; it contains no logic). The FIFO's
module name, its DEPTH parameter (8) and its other port names are your choice;
a first-word-fall-through FIFO whose output valid is "not empty" meets the
k+1 start rule. The mechanical top binds a child port to a top port only by
identical name, so the child facing the input stream must name its ports
`in_data`, `in_valid` and `in_ready`, `uart_tx` keeps `tx`, every child has
`clk` and `rst`, and no other child port may reuse a top port name. Connect
the FIFO's output byte and output valid to `uart_tx.tx_data` and
`uart_tx.tx_valid`, and `uart_tx.tx_ready` back to the FIFO's output ready,
with explicit connections.
