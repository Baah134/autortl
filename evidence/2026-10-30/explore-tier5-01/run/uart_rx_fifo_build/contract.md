# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (uart_rx_core, rx_fifo, rx_err_count) and the top uart_rx_fifo, children first and top last; no frozen companion is compiled beside it. Only the top uart_rx_fifo carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define uart_rx_fifo; modules the trusted testbench instantiates directly (rx_err_count, rx_fifo, uart_rx_core) must stay defined and be live-reached from uart_rx_fifo. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory.

## Verification gates

The current top's numeric latency is UNKNOWN, not zero. Its missing @latency annotation is neither FAIL nor INVESTIGATE and must not block ACCEPT. Do not invent a numeric top annotation from child typed-module metadata or an arbitrary aggregate wrapper. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

Use the frozen testbench unchanged. Pass static/interface and declared latency checks when a numeric declaration is known, xvlog compilation, xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, not zero; an annotation alone is not independent behavioral proof. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for timing closure and for promotion, except timing_progress below. Missing or unknown evidence is not success.

## Objective and completion

First establish timing feasibility: the candidate must pass simulation and all verification/metric/receipt gates, with timing_met=true, WNS >= 0 and WHS >= 0. A candidate meeting those gates may replace a previous verified best whose known consistent timing evidence fails setup or hold, even when area or power increases or stays equal. Classify this as timing_recovery: a feasibility recovery, not resource or power savings. Unknown, missing or contradictory timing evidence does not establish a timing recovery. While the previous best is still timing-infeasible, a verified candidate that is also infeasible may replace it only with strictly better setup WNS and hold WHS not worse beyond a small tolerance. Classify this as timing_progress: progress toward closure, not closure; a timing-feasible candidate always outranks it, a feasible previous best is never replaced by an infeasible candidate, and a run whose best is still infeasible has not closed timing. Once both designs are timing-feasible, objective minimize_luts maps to lut_used: require strictly lower than the previous verified best, under the same device, clock and constraints. No minimum percentage gain or extra slack margin is imposed. Final evaluator ACCEPT with zero failed criteria and all deterministic promotion gates are required. DONE describes a completed experiment; best_iteration 0 retains the baseline and claims no accepted improvement. Only a promoted best_iteration > 0 establishes an accepted improvement; its recorded kind distinguishes timing recovery and timing progress from objective gain.

## Fixed measurement authority

The JSON below records source/testbench identities, actual device, clock, tool context, constraints and retained report hashes. Numeric metrics are the parsed structured evidence, with routed reports preferred. The candidate's retained synthesis script records actual permitted retiming or physical optimization settings; these never change behavioral obligations.

```json
{
  "baseline_metrics": {
    "bram_total": 50.0,
    "bram_used": 0.0,
    "dsp_total": 90,
    "dsp_used": 0,
    "dynamic_power_w": 0.004,
    "ff_pct": 0.13221153846153846,
    "ff_total": 41600,
    "ff_used": 55,
    "lut_pct": 0.3125,
    "lut_total": 20800,
    "lut_used": 65,
    "reg2reg_wns_ns": 4.274,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.074,
    "whs_ns": 0.077,
    "wns_ns": -1.166
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\design_spec.json",
    "resolved_spec": {
      "connections": [
        {
          "dst_module": "rx_fifo",
          "dst_port": "wr_en",
          "src_module": "uart_rx_core",
          "src_port": "rx_strobe"
        },
        {
          "dst_module": "rx_fifo",
          "dst_port": "wr_data",
          "src_module": "uart_rx_core",
          "src_port": "rx_data"
        },
        {
          "dst_module": "rx_err_count",
          "dst_port": "ferr_in",
          "src_module": "uart_rx_core",
          "src_port": "frame_err"
        },
        {
          "dst_module": "rx_err_count",
          "dst_port": "ovf_in",
          "src_module": "rx_fifo",
          "src_port": "overflow"
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
          "name": "rx",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "out_data",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "out_valid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "out_ready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "frame_err",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "ferr_count",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 4
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "ovf_count",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 4
        }
      ],
      "modules": [
        {
          "behavior": "UART 8N1 receiver with 16x oversampling, a two-flop input synchronizer, a three-sample majority vote, start-bit validation and framing-error detection. Public parameter OVERSAMPLE_DIV=2 is the number of clk cycles per oversample tick; supported domain integer 1..64. Preserve the actual OVERSAMPLE_DIV-dependent timing, not only the default. Let D = OVERSAMPLE_DIV and B = 16*D (clk cycles per bit). Synchronizer: registers sync1 <= rx and sync2 <= sync1 at every rising edge, both reset to 1; the line sample L used at edge i is sync2 before edge i, i.e. rx as it was before edge i-2. States IDLE, BUSY and WAIT_IDLE; reset state IDLE. In IDLE the first edge with L = 0 is the detection edge e0 and enters BUSY. In BUSY, at edge e0 + m (m >= 1) the frame offset is m, the bit index is b = m div B (0 start bit, 1..8 data bits LSB first, 9 stop bit) and the phase is p = m mod B. At p = 7D, p = 8D and p = 9D the receiver takes L as three votes for bit b; at the p = 9D edge the bit value is the majority of the three votes and is decided at that edge. L at every other BUSY edge is ignored, so the line may carry anything there. Start bit (b = 0): majority 1 is a false start: return to IDLE at that edge with no output (the next edge may detect again); majority 0 continues the frame. Data bit b in 1..8 becomes received bit b-1 (LSB first). Stop bit (b = 9, decided at edge e0 + 153D): return to IDLE at that edge; majority 1 registers rx_data = the 8 received bits and pulses rx_strobe = 1 for exactly one cycle; majority 0 pulses frame_err = 1 for exactly one cycle, leaves rx_data unchanged and enters WAIT_IDLE. In WAIT_IDLE the first edge with L = 1 returns to IDLE without detecting, so a line held low produces exactly one framing error and a new frame can be detected at the following edge. Outputs are registers that change only at rising edges: rx_strobe and frame_err are 0 except for their one-cycle pulses, rx_data holds the last good byte (0 after reset). Synchronous active-high rst at a rising edge returns to IDLE and sets sync1 = sync2 = 1, rx_data = 0, rx_strobe = 0 and frame_err = 0; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge given the rx value present before that edge; keep sync1, sync2, the state, the frame offset, the votes and the received bits in state and return rx_data, rx_strobe and frame_err as registered by that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled. The examples hold rx constant from the reset state: with rx = 0 the detection edge is edge 3 (L lags rx by two edges), so with D = 2 the all-zero frame's stop bit is decided at edge 3 + 153*2 = 309, where frame_err pulses; frame_err is 0 again after edge 310 and the still-low line never re-triggers.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 40,
              "expected": {
                "frame_err": 0,
                "rx_data": 0,
                "rx_strobe": 0
              },
              "inputs": {
                "rst": 0,
                "rx": 1
              }
            },
            {
              "after_cycles": 309,
              "expected": {
                "frame_err": 1,
                "rx_data": 0,
                "rx_strobe": 0
              },
              "inputs": {
                "rst": 0,
                "rx": 0
              }
            },
            {
              "after_cycles": 310,
              "expected": {
                "frame_err": 0,
                "rx_data": 0,
                "rx_strobe": 0
              },
              "inputs": {
                "rst": 0,
                "rx": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "uart_rx_core",
          "parameters": {
            "OVERSAMPLE_DIV": 2
          },
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
              "name": "rx",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rx_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rx_strobe",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "frame_err",
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
          "behavior": "Synchronous first-word-fall-through byte FIFO with registered occupancy and an overflow pulse. Public parameter ADDR_BITS=2 sets the capacity DEPTH = 2^ADDR_BITS entries; supported domain integer 1..4; preserve the parameter. count is the number of stored bytes, 0..DEPTH. out_valid = (count != 0); out_data = the oldest stored byte when out_valid = 1 and 0 when out_valid = 0. Both depend only on registered state: there is no combinational path from wr_en, wr_data, out_ready or rst to any output. At each rising edge with rst low, using the inputs present before the edge: pop = out_ready && count != 0 removes the head byte; push = wr_en && (count < DEPTH || pop) stores wr_data behind all remaining bytes, so a full FIFO accepts a write at an edge where it also pops; a push and a pop at the same edge keep order and leave count unchanged. A byte written into an empty FIFO is visible after that edge, never in the same cycle (no bypass). overflow is a register: after an edge where wr_en = 1 and push = 0 (the byte is dropped) it is 1 for one cycle, otherwise 0. Synchronous active-high rst at a rising edge empties the FIFO and clears overflow; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the queue in state and return out_data, out_valid and overflow as they are after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state (empty) and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 60,
                "out_valid": 1,
                "overflow": 0
              },
              "inputs": {
                "out_ready": 0,
                "rst": 0,
                "wr_data": 60,
                "wr_en": 1
              }
            },
            {
              "after_cycles": 5,
              "expected": {
                "out_data": 60,
                "out_valid": 1,
                "overflow": 1
              },
              "inputs": {
                "out_ready": 0,
                "rst": 0,
                "wr_data": 60,
                "wr_en": 1
              }
            },
            {
              "after_cycles": 3,
              "expected": {
                "out_data": 167,
                "out_valid": 1,
                "overflow": 0
              },
              "inputs": {
                "out_ready": 1,
                "rst": 0,
                "wr_data": 167,
                "wr_en": 1
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rx_fifo",
          "parameters": {
            "ADDR_BITS": 2
          },
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
              "name": "wr_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "out_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "out_valid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "out_ready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "overflow",
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
          "behavior": "Two 4-bit saturating event counters. At each rising edge with rst low: if ferr_in = 1 and ferr_count < 15 then ferr_count increments by 1; if ovf_in = 1 and ovf_count < 15 then ovf_count increments by 1; a counter at 15 stays 15 (saturates, never wraps). Inputs are sampled only at rising edges and both outputs are registers. Synchronous active-high rst at a rising edge clears both counters; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep both counts in state and return ferr_count and ovf_count as registered by that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 3,
              "expected": {
                "ferr_count": 3,
                "ovf_count": 0
              },
              "inputs": {
                "ferr_in": 1,
                "ovf_in": 0,
                "rst": 0
              }
            },
            {
              "after_cycles": 20,
              "expected": {
                "ferr_count": 15,
                "ovf_count": 15
              },
              "inputs": {
                "ferr_in": 1,
                "ovf_in": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 16,
              "expected": {
                "ferr_count": 0,
                "ovf_count": 15
              },
              "inputs": {
                "ferr_in": 0,
                "ovf_in": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rx_err_count",
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
              "name": "ferr_in",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "ovf_in",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "ferr_count",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "ovf_count",
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
        }
      ],
      "top_name": "uart_rx_fifo"
    },
    "sha256": "64104e59b86927c238c5c776568af418d1e04b462969b9bc226e5df662133946",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\uart_rx_fifo.v",
    "source_sha256": "c8c910364d7d100b681811a57993d90520a7e14d941e955fb6284de345558cc6"
  },
  "edit_scope": {
    "children": [
      "uart_rx_core",
      "rx_fifo",
      "rx_err_count"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top uart_rx_fifo and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [
      "rx_err_count",
      "rx_fifo",
      "uart_rx_core"
    ],
    "top": "uart_rx_fifo"
  },
  "execution_context": {
    "dependencies": [],
    "part": "xc7a35tcpg236-1",
    "period_ns": 10.0,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR",
      "Synth 8-9873": "ERROR",
      "VRFC 10-3609": "ERROR"
    },
    "synthesis_template": "82fa3469b365c54e445b50a587f2dfd2ca06256e842bb05a2596faac46249cd4",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\inputs\\testbench_path.v",
      "sha256": "10f48bb3b8f77557a56f7825251e581d0054c067470ac9f48e823ac251f6008d"
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
    "top": "uart_rx_fifo"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\synth.tcl",
      "sha256": "d30a7f1a4ec63ea0d11683abfc9a0d0d9fb7d31e63924cf4d573715dbf39d38b",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/uart_rx_fifo.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing.xdc\"\r\nsynth_design -top uart_rx_fifo -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier5-01/uart_rx_fifo_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\power.rpt",
      "sha256": "7f697e997e660b9ff22a0354a7e4505678821e553db9d70059cf774355393786"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\timing.rpt",
      "sha256": "c60ca6ba3c01df3633a4899f838376b0ee4a9f8b64ad9d79a6295d48e18f39cb"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "3785f1d5424b20663d42222bc6e261090d5844370b3ef89dd559d54d6e3e22e4"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\timing_routed.rpt",
      "sha256": "db18413ecb6e4b9a37724a7f079384df0d60ef3cfd625cb138c4827fcef78677"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\utilization.rpt",
      "sha256": "2253f323f9c8134375f25dd78464e71afc4316fee939e18b8729a2cb67cf6bcc"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\utilization_routed.rpt",
      "sha256": "655cae6a940bc6e4cda2b134a19a25b9ffbc480ca6fb8a2903fe107389661187"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\iter_000\\uart_rx_fifo.v",
      "sha256": "c8c910364d7d100b681811a57993d90520a7e14d941e955fb6284de345558cc6"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier5-01\\uart_rx_fifo_build\\inputs\\testbench_path.v",
    "sha256": "10f48bb3b8f77557a56f7825251e581d0054c067470ac9f48e823ac251f6008d"
  },
  "testbench_top": "uart_rx_fifo_tb",
  "top_module": "uart_rx_fifo"
}
```
