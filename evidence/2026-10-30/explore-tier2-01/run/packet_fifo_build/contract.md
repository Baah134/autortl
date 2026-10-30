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
    "dynamic_power_w": 0.016,
    "ff_pct": 0.014423076923076924,
    "ff_total": 41600,
    "ff_used": 6,
    "lut_pct": 0.07211538461538461,
    "lut_total": 20800,
    "lut_used": 15,
    "reg2reg_wns_ns": 5.271,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.086,
    "whs_ns": 0.001,
    "wns_ns": -1.031
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\design_spec.json",
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
          "name": "in_last",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
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
          "name": "out_last",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
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
          "behavior": "Parameterized synchronous elastic packet-tagged FIFO, public parameters WIDTH=8 and DEPTH=3 in that order. Supported experiment domain: integer WIDTH 1..16 and DEPTH 1..8. Input/output data ports must remain symbolic [WIDTH-1:0]; last ports remain one bit. DEPTH controls actual capacity, pointer wrap and occupancy. Preserve all supported parameter behavior, not only defaults. At rising clk, synchronous active-high rst discards all queued tuples and overrides transfers; reset has no effect between edges. Otherwise accept the atomic tuple (in_data,in_last) on in_valid && in_ready and retire (out_data,out_last) on out_valid && out_ready sampled before the edge. out_valid equals (occupancy != 0), in_ready equals (occupancy < DEPTH) || out_ready. This is a combinational ready path; full simultaneous pop/push is legal and must preserve occupancy. While valid, out_data and out_last are exactly the oldest unretired accepted tuple, preserving order, multiplicity, every data bit and every last bit together. Keep out_valid, out_data and out_last stable under output stall until transfer or reset. Invalid out_data and out_last are unspecified. Last is an ordinary payload marker, not a handshake or a store-and-forward condition: present queued beats without waiting for a last-marked beat, allow zero or consecutive last markers, and never invent or infer a marker from the data. Reset may discard a partial packet without manufacturing a last-marked output. No empty bypass: a new tuple captured into an empty queue becomes valid only after capture, with earliest output transfer at the following edge (minimum age 1). Sustain one push and pop per cycle when nonempty and downstream ready. Explicitly wrap at DEPTH-1; do not assume power-of-two depth or truncate data to eight bits. For Python scoreboard oracle ONLY, each non-reset step represents one accepted input transaction: return its eventual identical out_data masked to default WIDTH and out_last masked to one bit. The oracle does not simulate occupancy, ready/valid scheduling, stalls or a delay queue; RTL must still implement all temporal behavior above. init() represents reset state and supplied rst must be handled. The independent temporal testbench checks the default wrapper and additional child parameter configurations.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "scoreboard",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 0,
                "out_last": 0
              },
              "inputs": {
                "in_data": 0,
                "in_last": 0,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 0,
                "out_last": 1
              },
              "inputs": {
                "in_data": 0,
                "in_last": 1,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 255,
                "out_last": 0
              },
              "inputs": {
                "in_data": 255,
                "in_last": 0,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 255,
                "out_last": 1
              },
              "inputs": {
                "in_data": 255,
                "in_last": 1,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 165,
                "out_last": 1
              },
              "inputs": {
                "in_data": 165,
                "in_last": 1,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 165,
                "out_last": 0
              },
              "inputs": {
                "in_data": 165,
                "in_last": 0,
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
                "name": "in_last",
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
                "name": "out_last",
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
          "name": "packet_fifo_core",
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
              "name": "in_last",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
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
              "name": "out_last",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
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
      "top_name": "packet_fifo"
    },
    "sha256": "76e3bc02bad38dd3275638a87afb7d90ef7ab2a0fa77d22abfade482cfde8332",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 1,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\packet_fifo.v",
    "source_sha256": "4d399dab329510e326dbd4c9da6143549921f4b6f41c1496f486a29fc475aae7"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\modules\\packet_fifo_core\\packet_fifo_core.v",
        "sha256": "435c66b167bb31a4724b914a7024b6f1464e2aae6803e34026346bdc389df3b0"
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
    "synthesis_template": "82fa3469b365c54e445b50a587f2dfd2ca06256e842bb05a2596faac46249cd4",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\inputs\\testbench_path.v",
      "sha256": "719498712a9307a1bddec2afad4b714800686419686ea937ed3b39663308baf1"
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
    "top": "packet_fifo"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\synth.tcl",
      "sha256": "66e1b1984e9d7e13c3efb8f45a43f628e4f8e33178b5568b387484f0f88c24d6",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/packet_fifo.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/modules/packet_fifo_core/packet_fifo_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing.xdc\"\r\nsynth_design -top packet_fifo -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier2-01/packet_fifo_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\power.rpt",
      "sha256": "8c67fdfcb513bed57b39aea27a6f05efcac00887b3d2c54502f0207948b331e7"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\timing.rpt",
      "sha256": "ef0c38478e2832500f1b8616452c048402f2919cab7845257d8f68f0a9661ed7"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "68927dae645dafebd06b55b337c9a5cddf55391e894ef9d075ec0cf73fc71de5"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\timing_routed.rpt",
      "sha256": "8c2f12553723b87c5e65d52954b9d5444521193f4c9cb7c887a90335d41a80b8"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\utilization.rpt",
      "sha256": "f6f8c0c1286c78beadd303263a516a98960531eb5f93dde8c03485c93a678b7b"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\utilization_routed.rpt",
      "sha256": "4eb8fb446219cf006072b1ea0c13bb124f779f2976255a9392137e9e669b8e98"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\iter_000\\packet_fifo.v",
      "sha256": "4d399dab329510e326dbd4c9da6143549921f4b6f41c1496f486a29fc475aae7"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\modules\\packet_fifo_core\\packet_fifo_core.v",
      "sha256": "435c66b167bb31a4724b914a7024b6f1464e2aae6803e34026346bdc389df3b0"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier2-01\\packet_fifo_build\\inputs\\testbench_path.v",
    "sha256": "719498712a9307a1bddec2afad4b714800686419686ea937ed3b39663308baf1"
  },
  "testbench_top": "packet_fifo_tb",
  "top_module": "packet_fifo"
}
```
