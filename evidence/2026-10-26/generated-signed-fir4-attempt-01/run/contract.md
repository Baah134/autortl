# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Verification gates

The current top has known numeric latency 3; require a matching // @latency 3 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "dynamic_power_w": 0.018,
    "ff_pct": 0.15865384615384615,
    "ff_total": 41600,
    "ff_used": 66,
    "lut_pct": 0.375,
    "lut_total": 20800,
    "lut_used": 78,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.088,
    "whs_ns": 0.029,
    "wns_ns": -0.327
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\design_spec.json",
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
          "name": "x",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": true,
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
          "signed": true,
          "width": 13
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
          "behavior": "Signed stateful FIR4 stream: every accepted input sample x[n] produces y[n]=3*x[n]-5*x[n-1]+7*x[n-2]-2*x[n-3]. x is signed8 [-128,127]; output is exact signed13, full range [-2169,2166], no saturation. The previous three ACCEPTED samples are initially/reset zero. Advance history ONLY when in_valid && in_ready before a rising edge; invalid or blocked samples never change it. Three elastic slots/capacity3: r3=!v3||out_ready, r2=!v2||r3, r1=!v1||r2, in_ready=r1, out_valid=v3. On a rising edge each ready stage takes OLD preceding stage valid/data; ready stage1 captures current input-valid and its FIR math on accepted input. No bypass. Capture edge k first becomes stage3-valid after edge k+2 when unobstructed, earliest transfer edge k+3 (minimum accepted-transfer age3). Sustain one accepted input and retired output per edge after filling including full retire/advance/replace. Stalls may delay outputs. Hold out_valid and defined signed result stable while blocked; invalid output payload unspecified. Synchronous active-high rst overrides transfers, clears all history and three valid slots ONLY at rising edges. Ready/valid reflect slot state even before an edge while rst asserted; no combinational reset gating. Entirely off-edge reset pulse has no effect on history or validity. Producer holds x and in_valid while blocked except reset abort. Python accepted-transaction oracle MUST keep three signed prior accepted samples in state, reinterpret masked8 input x>=128 as x-256, compute current FIR and advance history once per non-reset step. Return out_data masked13 (value &8191). Supplied rst clears history and returns0. Do NOT model pipeline/latency/validity/occupancy/backpressure in oracle. Each IOExample starts from zero history and after_cycles repeats the SAME accepted input; examples are first/repeated-constant anchors, not latency or an impulse trace.",
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
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0,
                "x": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 381
              },
              "inputs": {
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0,
                "x": 127
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "out_data": 7808
              },
              "inputs": {
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0,
                "x": 128
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "out_data": 7938
              },
              "inputs": {
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0,
                "x": 127
              }
            },
            {
              "after_cycles": 3,
              "expected": {
                "out_data": 7552
              },
              "inputs": {
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0,
                "x": 128
              }
            },
            {
              "after_cycles": 4,
              "expected": {
                "out_data": 381
              },
              "inputs": {
                "in_valid": 1,
                "out_ready": 1,
                "rst": 0,
                "x": 127
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 3,
          "latency_known": true,
          "name": "signed_fir4_core",
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
              "name": "x",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": true,
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
              "signed": true,
              "width": 13
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
      "top_name": "signed_fir4"
    },
    "sha256": "f64676a4330cb4c770e428dd6da0542992ab5c20d19b3d272ecc1056a6a21007",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 3,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\signed_fir4.v",
    "source_sha256": "ba3277b43c71e84669879f4d26da09a3ef68d2a15bd51ae6cb937f79bfc65f89"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\modules\\signed_fir4_core\\signed_fir4_core.v",
        "sha256": "2082c9466af6c4fb287b06d47244ce85d4ac0c729aeff03ee85852580a048be4"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\inputs\\testbench_path.v",
      "sha256": "125fb434d24bb69a363d5e5f693b183af06dce3caa83da374cbbdc1c821be244"
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
    "top": "signed_fir4"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\synth.tcl",
      "sha256": "d9032f3d8ea9d5319b2129ba6aad183c554257ca11f3a7b2006f177774ce4f6a",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/signed_fir4.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/modules/signed_fir4_core/signed_fir4_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/timing.xdc\"\r\nsynth_design -top signed_fir4 -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/timing_routed.rpt\"\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-signed-fir4-01/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\power.rpt",
      "sha256": "2a8cc453202aefd67ac7ba2c2cc59cf7671c5c049f74552d3528237be57ce82e"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\timing.rpt",
      "sha256": "877c87de7adc19856f69d10e7a646c6e6a7197e509e4436806ebb8944be93f52"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\timing_routed.rpt",
      "sha256": "bba6c1aa70ce02fd4e133d21f6a80e8ffad513cfb7e705ed86ab5dd382902148"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\utilization.rpt",
      "sha256": "80b6060d94c8ba3030f2bd452468c2fc5a35930984010dc3c28861622fcd4047"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\utilization_routed.rpt",
      "sha256": "d47261077ee6d6f873d160caf6cb6b2b41d27029c1803540f35dff6991899d9f"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\iter_000\\signed_fir4.v",
      "sha256": "ba3277b43c71e84669879f4d26da09a3ef68d2a15bd51ae6cb937f79bfc65f89"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\modules\\signed_fir4_core\\signed_fir4_core.v",
      "sha256": "2082c9466af6c4fb287b06d47244ce85d4ac0c729aeff03ee85852580a048be4"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-signed-fir4-01\\inputs\\testbench_path.v",
    "sha256": "125fb434d24bb69a363d5e5f693b183af06dce3caa83da374cbbdc1c821be244"
  },
  "testbench_top": "signed_fir4_tb",
  "top_module": "signed_fir4"
}
```
