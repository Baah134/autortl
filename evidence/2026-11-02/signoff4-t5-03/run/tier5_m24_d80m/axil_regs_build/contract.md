# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (axil_wr_if, axil_regbank, axil_rd_if) and the top axil_regs, children first and top last; no frozen companion is compiled beside it. Only the top axil_regs carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define axil_regs. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

## Implementation flow

Mode out_of_context, fixed by the harness. Out-of-context implementation (chip_top_flow_for_soc_block): the top is a block inside a larger design, synthesized with synth_design -mode out_of_context and placed and routed without I/O buffers or package pins. clk is constrained at the target period and modeled as driven by a global clock buffer (HD.CLK_SRC). Data ports have no input or output delay and no pad delay, so they are unconstrained I/O; the routed WNS and WHS, and timing acceptance, cover the internal clocked paths only, and combinational logic between a port and its first or last register is not timed. Utilization excludes I/O buffers.

## Verification gates

The current top's numeric latency is UNKNOWN, not zero. Its missing @latency annotation is neither FAIL nor INVESTIGATE and must not block ACCEPT. Do not invent a numeric top annotation from child typed-module metadata or an arbitrary aggregate wrapper. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

Use the frozen testbench unchanged. Pass static/interface and declared latency checks when a numeric declaration is known, xvlog compilation, xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, not zero; an annotation alone is not independent behavioral proof. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for timing closure and for promotion, except timing_progress below. Missing or unknown evidence is not success.

## Objective and completion

First establish timing feasibility: the candidate must pass simulation and all verification/metric/receipt gates, with timing_met=true, WNS >= 0 and WHS >= 0. A candidate meeting those gates may replace a previous verified best whose known consistent timing evidence fails setup or hold, even when area or power increases or stays equal. Classify this as timing_recovery: a feasibility recovery, not resource or power savings. Unknown, missing or contradictory timing evidence does not establish a timing recovery. While the previous best is still timing-infeasible, a verified candidate that is also infeasible may replace it only with strictly better setup WNS and hold WHS not worse beyond a small tolerance. Classify this as timing_progress: progress toward closure, not closure; a timing-feasible candidate always outranks it, a feasible previous best is never replaced by an infeasible candidate, and a run whose best is still infeasible has not closed timing. Once both designs are timing-feasible, objective minimize_luts maps to (lut_used, ff_used) compared lexicographically: require strictly lower lut_used, or equal lut_used with strictly lower ff_used, than the previous verified best, under the same device, clock and constraints. Higher lut_used is never an objective improvement. When either design lacks a finite ff_used, only strictly lower lut_used counts. No minimum percentage gain or extra slack margin is imposed. Final evaluator ACCEPT with zero failed criteria and all deterministic promotion gates are required. DONE describes a completed experiment; best_iteration 0 retains the baseline and claims no accepted improvement. Only a promoted best_iteration > 0 establishes an accepted improvement; its recorded kind distinguishes timing recovery and timing progress from objective gain.

## Fixed measurement authority

The JSON below records source/testbench identities, actual device, clock, tool context, constraints and retained report hashes. Numeric metrics are the parsed structured evidence, with routed reports preferred. The candidate's retained synthesis script records actual permitted retiming or physical optimization settings; these never change behavioral obligations.

```json
{
  "baseline_metrics": {
    "bram_total": 50.0,
    "bram_used": 0.0,
    "dsp_total": 90,
    "dsp_used": 0,
    "dynamic_power_w": 0.002,
    "ff_pct": 0.6105769230769231,
    "ff_total": 41600,
    "ff_used": 254,
    "lut_pct": 0.4567307692307692,
    "lut_total": 20800,
    "lut_used": 95,
    "reg2reg_wns_ns": 5.441,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.071,
    "whs_ns": 0.134,
    "wns_ns": 5.441
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\design_spec.json",
    "resolved_spec": {
      "connections": [
        {
          "dst_module": "axil_regbank",
          "dst_port": "wr_en",
          "src_module": "axil_wr_if",
          "src_port": "wr_en"
        },
        {
          "dst_module": "axil_regbank",
          "dst_port": "wr_idx",
          "src_module": "axil_wr_if",
          "src_port": "wr_idx"
        },
        {
          "dst_module": "axil_regbank",
          "dst_port": "wr_data",
          "src_module": "axil_wr_if",
          "src_port": "wr_data"
        },
        {
          "dst_module": "axil_regbank",
          "dst_port": "wr_strb",
          "src_module": "axil_wr_if",
          "src_port": "wr_strb"
        },
        {
          "dst_module": "axil_rd_if",
          "dst_port": "regs_flat",
          "src_module": "axil_regbank",
          "src_port": "regs_flat"
        }
      ],
      "external_ports": [
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "clk",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "rst",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "awvalid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "awready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "awaddr",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 6
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "wvalid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "wready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "wdata",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "wstrb",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 4
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "bvalid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "bready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "bresp",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 2
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "arvalid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "arready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "araddr",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 6
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rvalid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "rready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rdata",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rresp",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 2
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "irq_set",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "status_in",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "ctrl",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "irq",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        }
      ],
      "modules": [
        {
          "behavior": "AXI4-Lite slave write side: AW, W and B channels driving a register-bank write port. Byte addresses are 6 bits; awaddr[5] = 1 (0x20..0x3F) is out of range, awaddr[1:0] are ignored and the register index is awaddr[4:2]. State: aw_full with aw_addr[5:0]; w_full with w_data[31:0] and w_strb[3:0]; bvalid with bresp[1:0]; all reset to 0. Every output is a view of that state with no combinational path from any input: awready = !aw_full and wready = !w_full (the channels are independent; neither ready waits for the other channel's valid); bvalid and bresp are the registers; with do_write = aw_full && w_full && !bvalid, wr_en = do_write && !aw_addr[5]; wr_idx = aw_addr[4:2], wr_data = w_data and wr_strb = w_strb are shown whatever wr_en is. At each rising edge with rst low, using the state and inputs before the edge: if do_write then aw_full = 0, w_full = 0, bvalid = 1 and bresp = 2 (SLVERR) when aw_addr[5] = 1, else 0 (OKAY); the bank writes at this same edge, so the register update and the response become visible together, and an out-of-range write changes no register. Otherwise, if bvalid && bready then bvalid = 0. Independently, if awvalid && awready then aw_full = 1 and aw_addr = awaddr; if wvalid && wready then w_full = 1, w_data = wdata and w_strb = wstrb. So AW and W may arrive in either order or together, one of each may be held while a response is pending, and a held pair is written only at an edge where bvalid was 0 before the edge (not at the edge where a stalled response retires). A write costs at least two edges, so one write per two cycles is the peak rate. bresp keeps its value after the B transfer. Synchronous active-high rst at a rising edge returns every register to its reset value; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "awready": 0,
                "bresp": 0,
                "bvalid": 0,
                "wr_data": 305419896,
                "wr_en": 1,
                "wr_idx": 1,
                "wr_strb": 15,
                "wready": 0
              },
              "inputs": {
                "awaddr": 4,
                "awvalid": 1,
                "bready": 0,
                "rst": 0,
                "wdata": 305419896,
                "wstrb": 15,
                "wvalid": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "awready": 1,
                "bresp": 2,
                "bvalid": 1,
                "wr_data": 4294967295,
                "wr_en": 0,
                "wr_idx": 1,
                "wr_strb": 15,
                "wready": 1
              },
              "inputs": {
                "awaddr": 36,
                "awvalid": 1,
                "bready": 0,
                "rst": 0,
                "wdata": 4294967295,
                "wstrb": 15,
                "wvalid": 1
              }
            },
            {
              "after_cycles": 3,
              "expected": {
                "awready": 0,
                "bresp": 0,
                "bvalid": 0,
                "wr_data": 0,
                "wr_en": 0,
                "wr_idx": 2,
                "wr_strb": 0,
                "wready": 1
              },
              "inputs": {
                "awaddr": 8,
                "awvalid": 1,
                "bready": 1,
                "rst": 0,
                "wdata": 4294967295,
                "wstrb": 15,
                "wvalid": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "axil_wr_if",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "awvalid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "awready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "awaddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 6
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wvalid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wstrb",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "bvalid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "bready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "bresp",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 2
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_en",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_idx",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_strb",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "Bank of eight 32-bit registers behind one write port, exposed as a flat 256-bit view. Map by index (byte address 4*index): 0 CTRL read/write, reset 0, also driven on output ctrl; 1 SCRATCH read/write, reset 0; 2 CONFIG read/write, reset 0x00000100; 3 IRQ_MASK: bits 7:0 read/write, written only when wr_strb[0] = 1, bits 31:8 read 0, reset 0; 4 IRQ_STATUS: bits 7:0 pending flags, write-1-to-clear, bits 31:8 read 0, reset 0; 5 STATUS read-only: status_in as sampled at the previous rising edge (registered every cycle), reset 0; 6 ID read-only constant 0x52544C35; 7 WRITE_COUNT read-only: the number of edges with wr_en = 1 since reset (any index, any strobes), modulo 2^32, reset 0. regs_flat[32*i+31:32*i] = register i, ctrl = CTRL and irq = OR of the bits of (IRQ_STATUS[7:0] & IRQ_MASK[7:0]); all three depend only on registered state. At each rising edge with rst low, using pre-edge values: STATUS = status_in; IRQ_STATUS[7:0] = (IRQ_STATUS[7:0] & ~clear) | irq_set, where clear = wr_data[7:0] if wr_en && wr_idx == 4 && wr_strb[0], else 0, so a flag that is set and cleared at the same edge stays set; if wr_en then WRITE_COUNT increments, for index 0, 1 or 2 each byte lane b with wr_strb[b] = 1 takes byte b of wr_data and the other lanes keep their value, and for index 3 IRQ_MASK[7:0] = wr_data[7:0] when wr_strb[0] = 1; writes to indexes 5, 6 and 7 change nothing but still count. When wr_en = 0, wr_idx, wr_data and wr_strb are ignored. Synchronous active-high rst at a rising edge returns every register to its reset value; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "ctrl": 0,
                "irq": 0,
                "regs_flat": 35630232639653906037930654921732627050046000695818909790155757846528
              },
              "inputs": {
                "irq_set": 5,
                "rst": 0,
                "status_in": 51966,
                "wr_data": 255,
                "wr_en": 1,
                "wr_idx": 4,
                "wr_strb": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "ctrl": 10813605,
                "irq": 0,
                "regs_flat": 62590179306804469884203584469349798516392435866679209793910009561253
              },
              "inputs": {
                "irq_set": 0,
                "rst": 0,
                "status_in": 0,
                "wr_data": 2779096485,
                "wr_en": 1,
                "wr_idx": 0,
                "wr_strb": 5
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "ctrl": 0,
                "irq": 1,
                "regs_flat": 62590179306804469894434095974562544296822472923605921376553333161984
              },
              "inputs": {
                "irq_set": 129,
                "rst": 0,
                "status_in": 7,
                "wr_data": 4294967295,
                "wr_en": 1,
                "wr_idx": 3,
                "wr_strb": 15
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "axil_regbank",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wr_en",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wr_idx",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wr_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wr_strb",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "irq_set",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "status_in",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "regs_flat",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 256
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "ctrl",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "irq",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "AXI4-Lite slave read side: AR and R channels reading a flat view of eight 32-bit registers, where regs_flat[32*i+31:32*i] is register i. Byte addresses are 6 bits; araddr[5] = 1 (0x20..0x3F) is out of range, araddr[1:0] are ignored and the index is araddr[4:2]. State rvalid, rdata[31:0] and rresp[1:0], all reset to 0; arready = !rvalid, from registered state only. At each rising edge with rst low: if arvalid && !rvalid the read is accepted: rvalid = 1 and, when araddr[5] = 1, rdata = 0 and rresp = 2 (SLVERR), else rdata = register araddr[4:2] of regs_flat as it was before this edge and rresp = 0 (OKAY); otherwise, if rvalid && rready then rvalid = 0. While rvalid && !rready, rvalid, rdata and rresp hold whatever arvalid, araddr or regs_flat do, and rdata and rresp keep their values after the R transfer. The next read can be accepted at the edge after an R transfer at the earliest. Synchronous active-high rst at a rising edge returns every register to its reset value; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "arready": 0,
                "rdata": 2734883587,
                "rresp": 0,
                "rvalid": 1
              },
              "inputs": {
                "araddr": 8,
                "arvalid": 1,
                "regs_flat": 76002748785747371621271812474050423447790058081543318813521012657984242778369,
                "rready": 0,
                "rst": 0
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "arready": 0,
                "rdata": 0,
                "rresp": 2,
                "rvalid": 1
              },
              "inputs": {
                "araddr": 48,
                "arvalid": 1,
                "regs_flat": 76002748785747371621271812474050423447790058081543318813521012657984242778369,
                "rready": 0,
                "rst": 0
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "arready": 1,
                "rdata": 2819098632,
                "rresp": 0,
                "rvalid": 0
              },
              "inputs": {
                "araddr": 31,
                "arvalid": 1,
                "regs_flat": 76002748785747371621271812474050423447790058081543318813521012657984242778369,
                "rready": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "axil_rd_if",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "arvalid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "arready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "araddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 6
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rvalid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rresp",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 2
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "regs_flat",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 256
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        }
      ],
      "top_name": "axil_regs"
    },
    "sha256": "c5c678b7e163143a7183967cbb1395ef291866c9484c98333d6d8c7f93efba85",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\axil_regs.v",
    "source_sha256": "ff0ceb819f7c74dfcb06afb8a3224cf65ae9c750ff47414066b4216f25cd709d"
  },
  "edit_scope": {
    "children": [
      "axil_wr_if",
      "axil_regbank",
      "axil_rd_if"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top axil_regs and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [],
    "top": "axil_regs"
  },
  "execution_context": {
    "dependencies": [],
    "implementation": "out_of_context",
    "part": "xc7a35tcpg236-1",
    "period_ns": 10.0,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR",
      "Synth 8-9873": "ERROR",
      "VRFC 10-3609": "ERROR"
    },
    "synthesis_template": "61e44d95134130552d86e050a4db65035952d348028dc942b327b8aced90b3d1",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\inputs\\testbench_path.v",
      "sha256": "e2d993581d56e24d9111541f82e3d2a5f12dee802409a47ecfd52bf4d0e9eb74"
    },
    "tools": {
      "vivado_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\vivado.bat",
        "sha256": "4f9c05aea82a71c7086a9e5edf01ba16ea70255f69cf3420c58b805ec113e994"
      },
      "xelab_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\xelab.bat",
        "sha256": "512a29ace988992d7fab14ca84f20f0b4515bb69ef1d5fef0a57c5f28b72c9b1"
      },
      "xsim_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\xsim.bat",
        "sha256": "8819fbb54fdf9cbcaaf24c2bf72801b403d5c93e0990ba32408b56c666761d21"
      },
      "xvlog_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\xvlog.bat",
        "sha256": "512a29ace988992d7fab14ca84f20f0b4515bb69ef1d5fef0a57c5f28b72c9b1"
      }
    },
    "top": "axil_regs"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\synth.tcl",
      "sha256": "f70d8fbb23eaade9ff60e403eeb58c8e7a27ce32b4441f080ba4ba91bd20d0bd",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/axil_regs.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nputs $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/timing.xdc\"\r\nsynth_design -top axil_regs -flatten_hierarchy rebuilt -mode out_of_context \r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t5-03/tier5_m24_d80m/axil_regs_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\timing.xdc",
      "sha256": "64b6a06a567f5142e3b71c9ec44440c46d1ff02057a9207ab3820113a8e3e958",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\nset_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]\r\n",
      "truncated": false
    }
  ],
  "implementation": {
    "meaning": "Out-of-context implementation (chip_top_flow_for_soc_block): the top is a block inside a larger design, synthesized with synth_design -mode out_of_context and placed and routed without I/O buffers or package pins. clk is constrained at the target period and modeled as driven by a global clock buffer (HD.CLK_SRC). Data ports have no input or output delay and no pad delay, so they are unconstrained I/O; the routed WNS and WHS, and timing acceptance, cover the internal clocked paths only, and combinational logic between a port and its first or last register is not timed. Utilization excludes I/O buffers.",
    "mode": "out_of_context"
  },
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\power.rpt",
      "sha256": "2eaf65757e6ee36ad0178672809dec99c717076d56edf2e6d5c326e8ef100136"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\timing.rpt",
      "sha256": "c4f287c8843b37edfd1df63917e722a77781739ddc85b5db24d48611b616c51f"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "77e523691e741193713ad3ad093a1de2271e4861490a235a0edc8440407636ce"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\timing_routed.rpt",
      "sha256": "951596abaef6383fbfddf249107348ae8c8a1256cdd1be6d2f17406107541a76"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\utilization.rpt",
      "sha256": "f9496aab12b111c0726191dbd2d1487a5f4ef303f8a709b925449ad869ae6329"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\utilization_routed.rpt",
      "sha256": "be1a97798980e9348de2c7c288e37b3cea43a647e31b2ce980e560866486b5fc"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\iter_000\\axil_regs.v",
      "sha256": "ff0ceb819f7c74dfcb06afb8a3224cf65ae9c750ff47414066b4216f25cd709d"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t5-03\\tier5_m24_d80m\\axil_regs_build\\inputs\\testbench_path.v",
    "sha256": "e2d993581d56e24d9111541f82e3d2a5f12dee802409a47ecfd52bf4d0e9eb74"
  },
  "testbench_top": "axil_regs_tb",
  "top_module": "axil_regs"
}
```
