# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (iterative_divider_core) and the top iterative_divider, children first and top last; no frozen companion is compiled beside it. Only the top iterative_divider carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define iterative_divider; modules the trusted testbench instantiates directly (iterative_divider_core) must stay defined and be live-reached from iterative_divider. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

## Implementation flow

Mode chip_top, fixed by the harness. Chip-top implementation: the top is the whole FPGA design. Every port bit gets an I/O buffer on a package pin, and data ports have zero input and output delay to clk, so the routed WNS and WHS include pad delay. Utilization includes the I/O buffers.

## Verification gates

The current top has known numeric latency 9; require a matching // @latency 9 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "dynamic_power_w": 0.022,
    "ff_pct": 0.11298076923076923,
    "ff_total": 41600,
    "ff_used": 47,
    "lut_pct": 0.18269230769230768,
    "lut_total": 20800,
    "lut_used": 38,
    "reg2reg_wns_ns": 4.98,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.092,
    "whs_ns": 0.092,
    "wns_ns": 0.313
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\design_spec.json",
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
          "name": "dividend",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "divisor",
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
          "name": "quotient",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "remainder",
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
          "behavior": "Parameterized unsigned iterative divider, public parameter WIDTH=8. Supported experiment domain: integer WIDTH 1..16. Preserve unsigned symbolic [WIDTH-1:0] dividend, divisor, quotient and remainder ports and actual WIDTH-dependent arithmetic and schedule, not only defaults. Preferred implementation is restoring division with a WIDTH+1-bit trial remainder and one bounded arithmetic step per compute edge. Capture dividend and divisor only on in_valid && in_ready at rising edge k. There is one outstanding transaction. Define internal computing state busy and held-result flag out_valid: in_ready equals !busy && !out_valid, independent of out_ready and without combinational reset gating. During computing or while a result is held, do not accept another request. Execute exactly WIDTH compute iterations at edges k+1 through k+WIDTH; no arithmetic iteration occurs at capture. out_valid first becomes visible after the NBA update of edge k+WIDTH, with quotient and remainder final together. Earliest retirement is edge k+WIDTH+1; no early result for zero, divisor one, equal operands, dividend smaller than divisor, or divide by zero. At the edge that retires a held result, in_ready was false, so a new request cannot be accepted until a later edge (earliest the following edge). For nonzero divisor, quotient=floor(dividend/divisor) and remainder=dividend%divisor. For divisor zero, quotient is all WIDTH ones and remainder is the captured original dividend, on the same fixed schedule. Ignore operand/input-valid noise after capture until the next accepted transaction. Hold out_valid and the atomic quotient/remainder tuple stable while stalled, until transfer or reset; invalid output fields are unspecified. Synchronous active-high rst aborts computation and any held result at the rising edge and overrides all transfers. Reset has no effect between edges; do not gate handshake or output signals combinationally with rst. After reset, no abandoned result may appear. Numeric latency=9 and // @latency 9 describe only default WIDTH=8 minimum accepted-transfer age; overridden children must satisfy WIDTH+1 age and the exact availability schedule above, checked independently. For the Python scoreboard oracle ONLY, each non-reset step represents one accepted dividend/divisor pair: return its eventual unsigned quotient and remainder masked to default WIDTH, including the explicit divide-by-zero rule. The oracle is arithmetic, not a busy/ready scheduling model or delay queue; init() represents reset state and supplied rst must be handled. Independent temporal verification checks scheduling, stalls, aborts and selected parameter overrides. Behavioral tests establish arithmetic and schedule, not physical iterative structure; retain source review of the sequential implementation for that claim.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "scoreboard",
          "examples": [
            {
              "after_cycles": 9,
              "expected": {
                "quotient": 255,
                "remainder": 0
              },
              "inputs": {
                "dividend": 0,
                "divisor": 0,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 9,
              "expected": {
                "quotient": 255,
                "remainder": 255
              },
              "inputs": {
                "dividend": 255,
                "divisor": 0,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 9,
              "expected": {
                "quotient": 255,
                "remainder": 0
              },
              "inputs": {
                "dividend": 255,
                "divisor": 1,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 9,
              "expected": {
                "quotient": 15,
                "remainder": 15
              },
              "inputs": {
                "dividend": 255,
                "divisor": 16,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 9,
              "expected": {
                "quotient": 0,
                "remainder": 128
              },
              "inputs": {
                "dividend": 128,
                "divisor": 255,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 9,
              "expected": {
                "quotient": 12,
                "remainder": 0
              },
              "inputs": {
                "dividend": 144,
                "divisor": 12,
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
                "name": "dividend",
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
                "name": "divisor",
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
                "name": "quotient",
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
                "name": "remainder",
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
          "latency": 9,
          "latency_known": true,
          "name": "iterative_divider_core",
          "parameters": {
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
              "name": "dividend",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "divisor",
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
              "name": "quotient",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "remainder",
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
      "top_name": "iterative_divider"
    },
    "sha256": "f7652c21b4360894126a4d97746e470f3969db7b5f10d738f34a79985b7fb528",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 9,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\iterative_divider.v",
    "source_sha256": "69053543c6bd9ee9ba69a60860801db99ba5fcc6335a1d7e157de84b7e5c4363"
  },
  "edit_scope": {
    "children": [
      "iterative_divider_core"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top iterative_divider and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [
      "iterative_divider_core"
    ],
    "top": "iterative_divider"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\inputs\\testbench_path.v",
      "sha256": "aecd87a99a0976f74e8d1e1de7eb6c1d977a46b5c3b8d7d01d392340ec3e3039"
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
    "top": "iterative_divider"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\synth.tcl",
      "sha256": "f210d689ad51ac26bdd3e901aa8968533ce44d28cdb82d17f401dcb914c3c878",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/iterative_divider.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing.xdc\"\r\nsynth_design -top iterative_divider -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-01/tier3_6h_ol6d8/iterative_divider_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\timing_io.tcl",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\power.rpt",
      "sha256": "4fbb3c89361d273bbc96cb08d92c4093e30923444585d2a64a72f08afab9df0f"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\timing.rpt",
      "sha256": "1a13906a9b89b1400d8dd6f3009b6a15c4c24272dac5bfc3b17a234e2b07cccd"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "64b12bfa8a9bd5745c264496797bf05a1487b3048b75a7d0bf62e927be30ece8"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\timing_routed.rpt",
      "sha256": "ead3b1f0969706c947c95b13eb16507e48bbbd1db82b48beaafd626bf37ef619"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\utilization.rpt",
      "sha256": "fa299b6fd319d5bc97e9418673669ab0543865c98544113fc2fe23ac1d6be0e7"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\utilization_routed.rpt",
      "sha256": "bb7f8c3e0e437fc2022141e4cb95a8342ca8154caab8c255785308108ca18951"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\iter_000\\iterative_divider.v",
      "sha256": "69053543c6bd9ee9ba69a60860801db99ba5fcc6335a1d7e157de84b7e5c4363"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-01\\tier3_6h_ol6d8\\iterative_divider_build\\inputs\\testbench_path.v",
    "sha256": "aecd87a99a0976f74e8d1e1de7eb6c1d977a46b5c3b8d7d01d392340ec3e3039"
  },
  "testbench_top": "iterative_divider_tb",
  "top_module": "iterative_divider"
}
```
