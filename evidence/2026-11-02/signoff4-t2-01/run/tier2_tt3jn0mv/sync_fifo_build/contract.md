# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (sync_fifo_core) and the top sync_fifo, children first and top last; no frozen companion is compiled beside it. Only the top sync_fifo carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define sync_fifo; modules the trusted testbench instantiates directly (sync_fifo_core) must stay defined and be live-reached from sync_fifo. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

## Implementation flow

Mode chip_top, fixed by the harness. Chip-top implementation: the top is the whole FPGA design. Every port bit gets an I/O buffer on a package pin, and data ports have zero input and output delay to clk, so the routed WNS and WHS include pad delay. Utilization includes the I/O buffers.

## Verification gates

The current top has known numeric latency 1; require a matching // @latency 1 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "dynamic_power_w": 0.015,
    "ff_pct": 0.014423076923076924,
    "ff_total": 41600,
    "ff_used": 6,
    "lut_pct": 0.0625,
    "lut_total": 20800,
    "lut_used": 13,
    "reg2reg_wns_ns": 5.452,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.085,
    "whs_ns": 0.091,
    "wns_ns": -0.931
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\design_spec.json",
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
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "in_ready",
          "packed_dimensions": null,
          "protocol": "valid_ready",
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
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "out_ready",
          "packed_dimensions": null,
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        }
      ],
      "modules": [
        {
          "behavior": "Parameterized synchronous elastic FIFO, public parameters WIDTH=8 and DEPTH=3 in that order. Supported experiment domain: integer WIDTH 1..16 and DEPTH 1..8. Input/output payload ports must remain symbolic [WIDTH-1:0]; DEPTH controls actual capacity, pointer wrap and occupancy. Preserve all supported parameter behavior, not only defaults. At rising clk, synchronous active-high rst discards all queued words and overrides transfers; reset has no effect between edges. Otherwise accept input on in_valid && in_ready and retire output on out_valid && out_ready sampled before the edge. out_valid equals (occupancy != 0), in_ready equals (occupancy < DEPTH) || out_ready. This is a combinational ready path; full simultaneous pop/push is legal and must preserve occupancy. out_data is the oldest unretired accepted input whenever valid. Keep valid and payload stable under output stall until transfer or reset. Invalid out_data is unspecified. No empty bypass: a new word captured into an empty queue becomes valid only after capture, with earliest output transfer at the following edge (minimum age 1). Sustain one push and pop per cycle when nonempty and downstream ready. Explicitly wrap at DEPTH-1; do not assume power-of-two depth or truncate payloads to eight bits. For Python scoreboard oracle ONLY, each non-reset step represents one accepted input transaction: return its eventual identical out_data, masked to default WIDTH. The oracle does not simulate FIFO occupancy, ready/valid scheduling, stalls or a delay queue; RTL must still implement all temporal behavior above. init() represents reset state and supplied rst must be handled. The independent temporal testbench checks the default wrapper and additional child parameter configurations.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "scoreboard",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 0
              },
              "inputs": {
                "in_data": 0,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 255
              },
              "inputs": {
                "in_data": 255,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 165
              },
              "inputs": {
                "in_data": 165,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": {
            "localparams": [],
            "parameters": [
              {
                "default": "8",
                "name": "WIDTH",
                "type": ""
              },
              {
                "default": "3",
                "name": "DEPTH",
                "type": ""
              }
            ],
            "ports": [
              {
                "dimensions": [],
                "direction": "input",
                "name": "clk",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [],
                "direction": "input",
                "name": "rst",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [
                  [
                    "WIDTH - 1",
                    "0"
                  ]
                ],
                "direction": "input",
                "name": "in_data",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [],
                "direction": "input",
                "name": "in_valid",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [],
                "direction": "output",
                "name": "in_ready",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [
                  [
                    "WIDTH - 1",
                    "0"
                  ]
                ],
                "direction": "output",
                "name": "out_data",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [],
                "direction": "output",
                "name": "out_valid",
                "signed": false,
                "value_type": "logic"
              },
              {
                "dimensions": [],
                "direction": "input",
                "name": "out_ready",
                "signed": false,
                "value_type": "logic"
              }
            ],
            "version": 1
          },
          "latency": 1,
          "latency_known": true,
          "name": "sync_fifo_core",
          "parameters": {
            "DEPTH": 3,
            "WIDTH": 8
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
              "protocol": "valid_ready",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "in_ready",
              "packed_dimensions": null,
              "protocol": "valid_ready",
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
              "protocol": "valid_ready",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "out_ready",
              "packed_dimensions": null,
              "protocol": "valid_ready",
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
      "top_name": "sync_fifo"
    },
    "sha256": "a7a1864a656a6aae6cb17fabda0b15e2314604c23384009bfc2a2a522a1199fc",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 1,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\sync_fifo.v",
    "source_sha256": "a007c2f177609312a11267f90f6acc6d5ca86be0df93559ef7ca318d62de452e"
  },
  "edit_scope": {
    "children": [
      "sync_fifo_core"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top sync_fifo and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [
      "sync_fifo_core"
    ],
    "top": "sync_fifo"
  },
  "execution_context": {
    "dependencies": [],
    "implementation": "chip_top",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\inputs\\testbench_path.v",
      "sha256": "2f5e867ee5421845b0e06565e7041a86c034afc78988701b09d684b2d0bb9139"
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
    "top": "sync_fifo"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\synth.tcl",
      "sha256": "4f2756abb9b682dc02510d4a0ee0086a8db711928cb1c65e695e2d62b7684ee6",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/sync_fifo.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing.xdc\"\r\nsynth_design -top sync_fifo -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-01/tier2_tt3jn0mv/sync_fifo_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "implementation": {
    "meaning": "Chip-top implementation: the top is the whole FPGA design. Every port bit gets an I/O buffer on a package pin, and data ports have zero input and output delay to clk, so the routed WNS and WHS include pad delay. Utilization includes the I/O buffers.",
    "mode": "chip_top"
  },
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\power.rpt",
      "sha256": "beb6b54f51b786912cf51370b9af806cd91439cd73fded5ffb5fbb4fb9fe89ad"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\timing.rpt",
      "sha256": "dfc6863a2f9e97c1c195134c817be47d99abbd1f073dd7afd20c17556fec3a8d"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "eb2622e67a9629b29f92536b2287d801dc42f77a30c960b1f2b1d1ab024d183c"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\timing_routed.rpt",
      "sha256": "5c027e735c3f7def24c4e8f40991dd2b1623a1cb1eca5b956db62f869434a6ff"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\utilization.rpt",
      "sha256": "84c00a86f7b9665a209132e7f9fabf68b93d47be8a7e59bd543bb50d9ca0596e"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\utilization_routed.rpt",
      "sha256": "801c335c47037b33397246ca83d35b4440d6839136597b993b77dcdb8edcb8d6"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\iter_000\\sync_fifo.v",
      "sha256": "a007c2f177609312a11267f90f6acc6d5ca86be0df93559ef7ca318d62de452e"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-01\\tier2_tt3jn0mv\\sync_fifo_build\\inputs\\testbench_path.v",
    "sha256": "2f5e867ee5421845b0e06565e7041a86c034afc78988701b09d684b2d0bb9139"
  },
  "testbench_top": "sync_fifo_tb",
  "top_module": "sync_fifo"
}
```
