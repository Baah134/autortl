# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Verification gates

The current top has known numeric latency 0; require a matching // @latency 0 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "dynamic_power_w": 0.003,
    "ff_pct": 0.014423076923076924,
    "ff_total": 41600,
    "ff_used": 6,
    "lut_pct": 0.028846153846153848,
    "lut_total": 20800,
    "lut_used": 6,
    "reg2reg_wns_ns": 6.587,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.073,
    "whs_ns": 0.219,
    "wns_ns": 0.731
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\design_spec.json",
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
          "name": "noisy",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "clean",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        }
      ],
      "modules": [
        {
          "behavior": "After reset, clean is 0. Track consecutive clock cycles for which noisy holds a value; update clean to that value only after it has held continuously for 8 cycles. Until then, clean holds its previous value. A change in noisy restarts the consecutive-cycle count.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 7,
              "expected": {
                "clean": 0
              },
              "inputs": {
                "noisy": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 8,
              "expected": {
                "clean": 1
              },
              "inputs": {
                "noisy": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 0,
          "latency_known": true,
          "name": "debouncer",
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
              "name": "noisy",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "clean",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
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
      "top_name": "debouncer_top"
    },
    "sha256": "e8ef78f821d1dbe9bca8d224cec77bc56bf31c707dedfd8d51760a9ffdb98564",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 0,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\debouncer_top.v",
    "source_sha256": "fcd15057f7008543f609741c041dfff2011b88d4bda20a1fe70669b19c2ef1f0"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\modules\\debouncer\\debouncer.v",
        "sha256": "98cfa5882d9815e82fa5e34547be50da94b3953e4f95efc5826ad62b1fc7c0e9"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\debouncer_top_tb.v",
      "sha256": "d6d0e66aca34223c359aeb8a5a3c82afe8e30e6d238d82a7faa285a99c634ac0"
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
    "top": "debouncer_top"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\synth.tcl",
      "sha256": "6447c0e35a911130d0650d7b861e46a5e2b3eea7e380c6b7747556320dac9087",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/debouncer_top.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/modules/debouncer/debouncer.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing.xdc\"\r\nsynth_design -top debouncer_top -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/tier1-campaign-03/tier1_0701k1s4/debouncer_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\power.rpt",
      "sha256": "63ff6f6fd2b2250d12fcac0c899776986c37e8abb93af2bd125408c8e6d6d968"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\timing.rpt",
      "sha256": "6adcd31d9304825200d770a24221c8a84b2f3dc562f91bab80d24b761d8afaaa"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "e7d334afc802312c048fb4fa9aab0e554c3beb4536378599abf02627b348e73d"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\timing_routed.rpt",
      "sha256": "4f5cc93b581430d3d65d3366744470d3ec4f943483ea5402a9e81d280aef8b9b"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\utilization.rpt",
      "sha256": "8051c5f5c2f4f515a43c371b5e176f6d513d9711d4b8b4c4c8c1e2b139102449"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\utilization_routed.rpt",
      "sha256": "7fd49f172517ebcea5d5769af0c7834f7b16dc78ed23211df9516d081d084018"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\iter_000\\debouncer_top.v",
      "sha256": "fcd15057f7008543f609741c041dfff2011b88d4bda20a1fe70669b19c2ef1f0"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\modules\\debouncer\\debouncer.v",
      "sha256": "98cfa5882d9815e82fa5e34547be50da94b3953e4f95efc5826ad62b1fc7c0e9"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\tier1-campaign-03\\tier1_0701k1s4\\debouncer_build\\debouncer_top_tb.v",
    "sha256": "d6d0e66aca34223c359aeb8a5a3c82afe8e30e6d238d82a7faa285a99c634ac0"
  },
  "testbench_top": "debouncer_top_tb",
  "top_module": "debouncer_top"
}
```
