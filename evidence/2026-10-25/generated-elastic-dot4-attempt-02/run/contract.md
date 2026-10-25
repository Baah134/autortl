# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Verification gates

The current top has known numeric latency 2; require a matching // @latency 2 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "dynamic_power_w": 0.067,
    "ff_pct": 0.12980769230769232,
    "ff_total": 41600,
    "ff_used": 54,
    "lut_pct": 1.5769230769230769,
    "lut_total": 20800,
    "lut_used": 328,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.138,
    "whs_ns": 0.112,
    "wns_ns": -0.052
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\design_spec.json",
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
          "name": "a0",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "b0",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "a1",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "b1",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "a2",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "b2",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "a3",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "b3",
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
          "width": 18
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
          "behavior": "Two-stage elastic unsigned dot-product pipeline. Compute a0*b0+a1*b1+a2*b2+a3*b3 exactly, output 0..260100. All eight operands are unsigned 8-bit, products16-bit, pair sums17-bit and final sum18-bit, preserve carries. Exactly two slots: stage1 holds two partial sums and valid v1; stage2 holds result and valid v2. out_valid=v2, stage2_ready=!v2||out_ready, in_ready=!v1||stage2_ready. Handshakes sample before rising-edge updates. On a rising edge, if stage2_ready update v2 from old v1 and when old v1 true capture sum of old partials. If in_ready update v1 from in_valid and when in_valid true capture current tuple's partials. Never bypass stage1 to output. Input captured at edge k is first output-valid after edge k+1 if stage2 can advance; earliest retirement at edge k+2 (minimum accepted-transfer age2). Bubbles and output stalls can delay transfers. Sustain one accepted input and output per edge after filling; support full simultaneous retire/advance/replace. Capacity2, not combinational empty bypass. Output-valid is stage2 occupancy, NOT total nonempty. On rising-edge synchronous active-high rst clear both valid slots, abort outstanding transactions, and override all transfers. Reset does not gate valid/ready combinationally or clear state between edges; an entirely off-edge reset pulse has no effect. Keep valid and defined output payload stable while stalled until transfer or synchronous reset. Invalid out_data is unspecified. Inputs are captured only on input handshake; producer holds in_valid and ALL eight operands stable while blocked, except reset abort. For the Python scoreboard oracle ONLY, one non-reset step maps an accepted eight-operand tuple directly to eventual out_data; no valid bits, occupancy, pipeline queue, scheduling or delay in oracle. init represents reset; supplied rst returns out_data=0. RTL must implement all temporal behavior above; independent TB verifies exact availability, capacity, throughput and resets.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "scoreboard",
          "examples": [
            {
              "after_cycles": 2,
              "expected": {
                "out_data": 260100
              },
              "inputs": {
                "a0": 255,
                "a1": 255,
                "a2": 255,
                "a3": 255,
                "b0": 255,
                "b1": 255,
                "b2": 255,
                "b3": 255,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "out_data": 0
              },
              "inputs": {
                "a0": 0,
                "a1": 0,
                "a2": 0,
                "a3": 0,
                "b0": 0,
                "b1": 0,
                "b2": 0,
                "b3": 0,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "out_data": 97667
              },
              "inputs": {
                "a0": 128,
                "a1": 1,
                "a2": 255,
                "a3": 1,
                "b0": 255,
                "b1": 1,
                "b2": 255,
                "b3": 1,
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 2,
          "latency_known": true,
          "name": "elastic_dot4_core",
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
              "name": "a0",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "b0",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "a1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "b1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "a2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "b2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "a3",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "b3",
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
              "width": 18
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
      "top_name": "elastic_dot4"
    },
    "sha256": "57464e772b728095a903772280b76df5c93d2fec981e1af6c3333f66a007353b",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 2,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\elastic_dot4.v",
    "source_sha256": "8c24cda14c69f2f2d6c32cb43f49e49bcaa19e46f951c31a7a4f3707a6cfc9e2"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\modules\\elastic_dot4_core\\elastic_dot4_core.v",
        "sha256": "e578e3c5afb22d6f7268a0a1c35a76cca4313fdeff02ab82cae4eb7cdffa6f1c"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\inputs\\testbench_path.v",
      "sha256": "cdf2445257187b2b708a408cdc8da7dfd178787e1eb4741a92a5dc3ab74a3eed"
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
    "top": "elastic_dot4"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\synth.tcl",
      "sha256": "ed6240fe0c5f5167ecc06aa51b1c7ee4e7d991396c548cbba0b17f5ecab111d5",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/elastic_dot4.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/modules/elastic_dot4_core/elastic_dot4_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/timing.xdc\"\r\nsynth_design -top elastic_dot4 -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/timing_routed.rpt\"\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-elastic-dot4-02/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\power.rpt",
      "sha256": "2a08cf8903efb0ff9d69ed0edb7564e14cc5c3a5a0ecee3521297d86d0cfc5d4"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\timing.rpt",
      "sha256": "51a60683c37b57c7ec95dbaeddad96b551521fa1db3ab1d1bb0d04f5d8607610"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\timing_routed.rpt",
      "sha256": "54ac54aee38d469cc510ded797370eda2d4ae34ba55c9a76f7b16c1e632ec53e"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\utilization.rpt",
      "sha256": "145ee3260e50bf38e7439a9bf26bae445c05951c31a7c748e9e506ec476524e9"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\utilization_routed.rpt",
      "sha256": "11b078c5e525daf8e64cf642087dc2a1d782cca8018cb4f4873fb2c95a63dfa6"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\iter_000\\elastic_dot4.v",
      "sha256": "8c24cda14c69f2f2d6c32cb43f49e49bcaa19e46f951c31a7a4f3707a6cfc9e2"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\modules\\elastic_dot4_core\\elastic_dot4_core.v",
      "sha256": "e578e3c5afb22d6f7268a0a1c35a76cca4313fdeff02ab82cae4eb7cdffa6f1c"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-elastic-dot4-02\\inputs\\testbench_path.v",
    "sha256": "cdf2445257187b2b708a408cdc8da7dfd178787e1eb4741a92a5dc3ab74a3eed"
  },
  "testbench_top": "elastic_dot4_tb",
  "top_module": "elastic_dot4"
}
```
