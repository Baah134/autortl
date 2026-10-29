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
    "dynamic_power_w": 0.006,
    "ff_pct": 0.019230769230769232,
    "ff_total": 41600,
    "ff_used": 8,
    "lut_pct": 0.028846153846153848,
    "lut_total": 20800,
    "lut_used": 6,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.077,
    "whs_ns": 0.226,
    "wns_ns": 0.424
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\design_spec.json",
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
          "name": "enable",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "count",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        }
      ],
      "modules": [
        {
          "behavior": "At each rising clk edge synchronous active-high rst sets count=0, else enable increments count modulo 256, else hold. Reset has priority. No changes between clock edges.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "count": 0
              },
              "inputs": {
                "enable": 1,
                "rst": 1
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "count": 1
              },
              "inputs": {
                "enable": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "counter8_core",
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
              "name": "enable",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "count",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 5,
            "kind": "sync",
            "signal": "rst"
          }
        }
      ],
      "top_name": "counter8"
    },
    "sha256": "4aaa3013f36e735ba9153eebd1e4c14539b3c0ada44620cdf2603112af82fea6",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 1,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\counter8.v",
    "source_sha256": "a7189dfa39a1198103a23ab2d15100320265f9fee332174e470d7258d5c40259"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\modules\\counter8_core\\counter8_core.v",
        "sha256": "b48f3d77a0a60c2217191c05a7c372cdf459fb352920a0e862ad7222925c07fa"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\inputs\\testbench_path.v",
      "sha256": "71e7d6f2664cc00749077b18c6cd4cdaa05ea38f893a321767c58f2bca7b76ae"
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
    "top": "counter8"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\synth.tcl",
      "sha256": "2e06c81a7c41434c88a3188d94bbea6e01aef5320a33a44eb52a4167689cb02b",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/counter8.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/modules/counter8_core/counter8_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/timing.xdc\"\r\nsynth_design -top counter8 -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/timing_routed.rpt\"\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-01/tier1_9gni9l_n/counter8_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\power.rpt",
      "sha256": "6c8ef7bea3783697cd7a9242c76366ee6ba5c168dd5eea098c9ffe23e5bf99ef"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\timing.rpt",
      "sha256": "107a36cb0eb912dd1a06de3714047b1f669227dda52c38be3e5fdfa9f2ba4e45"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\timing_routed.rpt",
      "sha256": "838ac057f4f73a1b5f898b38c9082c9786e1ba6afb86cc1ac6188640ca635d70"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\utilization.rpt",
      "sha256": "347621cc9391a99ec6d3e4e131811aee5597aabe46b0ca7a92a930b66d5aee0e"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\utilization_routed.rpt",
      "sha256": "56231d604dd3399f2e0b4df89cce60a91dca1106e63b0494b81dc4c41c81dcc5"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\iter_000\\counter8.v",
      "sha256": "a7189dfa39a1198103a23ab2d15100320265f9fee332174e470d7258d5c40259"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\modules\\counter8_core\\counter8_core.v",
      "sha256": "b48f3d77a0a60c2217191c05a7c372cdf459fb352920a0e862ad7222925c07fa"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-01\\tier1_9gni9l_n\\counter8_build\\inputs\\testbench_path.v",
    "sha256": "71e7d6f2664cc00749077b18c6cd4cdaa05ea38f893a321767c58f2bca7b76ae"
  },
  "testbench_top": "counter8_tb",
  "top_module": "counter8"
}
```
