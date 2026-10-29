# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Verification gates

The current top has known numeric latency 1; require a matching // @latency 1 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

Use the frozen testbench unchanged. Pass static/interface and declared latency checks when a numeric declaration is known, xvlog compilation, xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, not zero; an annotation alone is not independent behavioral proof. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for promotion. Missing or unknown evidence is not success.

## Objective and completion

First establish timing feasibility: the candidate must pass simulation and all verification/metric/receipt gates, with timing_met=true, WNS >= 0 and WHS >= 0. A candidate meeting those gates may replace a previous verified best whose known consistent timing evidence fails setup or hold, even when area or power increases or stays equal. Classify this as timing_recovery: a feasibility recovery, not resource or power savings. Unknown, missing or contradictory timing evidence does not establish a timing recovery. Once both designs are timing-feasible, objective minimize_luts maps to lut_used: require strictly lower than the previous verified best, under the same device, clock and constraints. No minimum percentage gain or extra slack margin is imposed. Final evaluator ACCEPT with zero failed criteria and all deterministic promotion gates are required. DONE describes a completed experiment; best_iteration 0 retains the baseline and claims no accepted improvement. Only a promoted best_iteration > 0 establishes an accepted improvement; its recorded kind distinguishes timing recovery from objective gain.

## Fixed measurement authority

The JSON below records source/testbench identities, actual device, clock, tool context, constraints and retained report hashes. Numeric metrics are the parsed structured evidence, with routed reports preferred. The candidate's retained synthesis script records actual permitted retiming or physical optimization settings; these never change behavioral obligations.

```json
{
  "baseline_metrics": {
    "bram_total": 50.0,
    "bram_used": 0.0,
    "dsp_total": 90,
    "dsp_used": 0,
    "dynamic_power_w": 0.012,
    "ff_pct": 0.0673076923076923,
    "ff_total": 41600,
    "ff_used": 28,
    "lut_pct": 0.19230769230769232,
    "lut_total": 20800,
    "lut_used": 40,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.082,
    "whs_ns": 0.141,
    "wns_ns": 0.702
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\design_spec.json",
    "resolved_spec": {
      "connections": [],
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
          "name": "in_data",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "in_valid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "in_ready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "tx",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        }
      ],
      "modules": [
        {
          "behavior": "UART 8N1 transmitter with a valid/ready byte input and a shortened stop bit, public parameter DIV=868 (clock cycles per bit; 868 gives 115200 baud from a 100 MHz clock), supported experiment domain integer DIV 16..4096. Define STOP = DIV - DIV/16 using integer division (814 at the default). Ports: in_data[7:0], in_valid, in_ready (output), tx (output, the serial line). Idle: tx=1 and in_ready=1. A byte is accepted at rising edge k when in_valid && in_ready && !rst; in_data is captured at that edge and later input changes are ignored until the frame ends. Bits are sent least significant data bit first: bit 0 is the start bit (0), bits 1..8 are in_data[0]..in_data[7], bit 9 is the stop bit (1). For i in 0..9, bit i is visible on tx after the NBA update of edge k+i*DIV. Bits 0..8 last exactly DIV cycles each; the stop bit lasts STOP cycles: after the NBA update of edge k+9*DIV+STOP the transmitter is idle again (tx=1, in_ready=1). The earliest next accept is edge k+9*DIV+STOP+1, so back-to-back frames repeat every 9*DIV+STOP+1 cycles (8627 at the default), which keeps up with a sender running up to 0.6% fast. in_ready is 0 from after edge k until that idle edge. in_valid while busy is ignored, not queued. tx and in_ready are registered outputs: they change only at rising edges, never combinationally from inputs or from rst. Synchronous active-high rst at a rising edge aborts any frame and returns to idle (tx=1, in_ready=1) and overrides an accept at the same edge; it has no effect between edges. The top uart_tx is the board configuration, fixed at the default DIV=868, and the trusted testbench checks the top only. For the Python golden model, each non-reset step is one clock edge with that step's inputs, returning tx and in_ready after the edge.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "in_ready": 1,
                "tx": 1
              },
              "inputs": {
                "in_data": 85,
                "in_valid": 1,
                "rst": 1
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "in_ready": 1,
                "tx": 1
              },
              "inputs": {
                "in_data": 85,
                "in_valid": 0,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "in_ready": 0,
                "tx": 0
              },
              "inputs": {
                "in_data": 85,
                "in_valid": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 869,
              "expected": {
                "in_ready": 0,
                "tx": 1
              },
              "inputs": {
                "in_data": 85,
                "in_valid": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1737,
              "expected": {
                "in_ready": 0,
                "tx": 0
              },
              "inputs": {
                "in_data": 85,
                "in_valid": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "uart_tx_core",
          "parameters": {
            "DIV": 868
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
              "name": "in_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "in_valid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "in_ready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "tx",
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
        }
      ],
      "top_name": "uart_tx"
    },
    "sha256": "bad1dec61cd43cb36932ca7ae1772189480f0e6f3cdb5e124f8e207656567c9d",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 1,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\uart_tx.v",
    "source_sha256": "ae30ae0468875361d182db18533f202b731d577619b8ceb8de945a39fc9a91a1"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\modules\\uart_tx_core\\uart_tx_core.v",
        "sha256": "75e3f28153285ad9e15152de9d9258454cc3658072019522de5d825b6d1b6e55"
      }
    ],
    "part": "xc7a35tcpg236-1",
    "period_ns": 10.0,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR",
      "Synth 8-9873": "ERROR",
      "VRFC 10-3609": "ERROR"
    },
    "synthesis_template": "c9d0bf78e20ec5b5854a3e48a12cb9d6ce15be79e660b27b3bf703670a77197a",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\inputs\\testbench_path.v",
      "sha256": "27a404f6295b1e6feea17ce2ea969c9ed2f9fd60713b3c8ec0f1d9b38bd69090"
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
    "top": "uart_tx"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\synth.tcl",
      "sha256": "62069d5cc7bc713924bd122ecbce47847b7a7886b00093b9bcc8605ee3812f12",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/uart_tx.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/modules/uart_tx_core/uart_tx_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/timing.xdc\"\r\nsynth_design -top uart_tx -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/timing_routed.rpt\"\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/harness-uart-tx-v2-01/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\power.rpt",
      "sha256": "1c5a9d668a9002a6d2dd89bb27d6d841e714bfc6c2c2ad9e427eeab59a932771"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\timing.rpt",
      "sha256": "e1785f70b91c55258e9b93df31b7e24cae2a5f0ef1ecb3bc60e84aa6501c3a40"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\timing_routed.rpt",
      "sha256": "d494bb7df87ed4d1559d1448e73db61adbd0475d701d1279405841b8738b2d44"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\utilization.rpt",
      "sha256": "f69c14ab81b0f8aa22dbb33597b3fd2303072b1b3feac1e5b0aafe686495fa62"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\utilization_routed.rpt",
      "sha256": "c9fa94e9cb23d2a946e636d8540d4a8a61f8d28b167a935d5461b1c340d1ec95"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\iter_000\\uart_tx.v",
      "sha256": "ae30ae0468875361d182db18533f202b731d577619b8ceb8de945a39fc9a91a1"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\modules\\uart_tx_core\\uart_tx_core.v",
      "sha256": "75e3f28153285ad9e15152de9d9258454cc3658072019522de5d825b6d1b6e55"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\harness-uart-tx-v2-01\\inputs\\testbench_path.v",
    "sha256": "27a404f6295b1e6feea17ce2ea969c9ed2f9fd60713b3c8ec0f1d9b38bd69090"
  },
  "testbench_top": "uart_tx_tb",
  "top_module": "uart_tx"
}
```
