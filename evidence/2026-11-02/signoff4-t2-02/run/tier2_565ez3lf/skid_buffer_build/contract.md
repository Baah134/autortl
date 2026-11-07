# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (skid_buffer_core) and the top skid_buffer, children first and top last; no frozen companion is compiled beside it. Only the top skid_buffer carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define skid_buffer. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

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
    "dynamic_power_w": 0.014,
    "ff_pct": 0.009615384615384616,
    "ff_total": 41600,
    "ff_used": 4,
    "lut_pct": 0.057692307692307696,
    "lut_total": 20800,
    "lut_used": 12,
    "reg2reg_wns_ns": 5.74,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.084,
    "whs_ns": 0.109,
    "wns_ns": -0.753
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\design_spec.json",
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
          "behavior": "Two-entry 8-bit elastic FIFO with no combinational data/valid fallthrough. At each rising clk edge, synchronous active-high rst discards all queued words and overrides all transfers. Reset must not clear state between edges. Outside reset, accept input iff in_valid && in_ready and retire output iff out_valid && out_ready, sampled BEFORE the edge. out_valid equals (occupancy != 0). in_ready equals (occupancy < 2) || out_ready, including simultaneous pop/push when full. This is an explicitly combinational ready path, not registered-ready isolation. out_data is the oldest unretired accepted input whenever out_valid is high; order, full 8-bit values and multiplicity must be preserved. While stalled, keep out_valid asserted and out_data unchanged until transfer or reset. Data when out_valid is low is unspecified. Newly accepted input into an empty queue becomes visible after that capture edge; earliest output handshake is the following edge (minimum one-cycle transaction latency), never a same-edge empty bypass. Sustain one accepted input and output every cycle when nonempty and downstream ready. No ports, parameters, extra cycles or capacity changes. For the Python scoreboard payload oracle ONLY: one step maps one accepted in_data to its eventual identical out_data; do not simulate FIFO occupancy, stalls or backpressure in that oracle. RTL still implements all cycle-level queue behavior above; the harness/testbench schedules handshakes.",
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
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "skid_buffer_core",
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
      "top_name": "skid_buffer"
    },
    "sha256": "b55473ba70327a4d3321e5f2767197fa3e50eab818bd370d9cc47f925222d105",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 1,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\skid_buffer.v",
    "source_sha256": "db2d6a1ef9ecc8d6d5d06b2aee4c89fbb212d584c79ac82d12001cb969b2438d"
  },
  "edit_scope": {
    "children": [
      "skid_buffer_core"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top skid_buffer and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [],
    "top": "skid_buffer"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\inputs\\testbench_path.v",
      "sha256": "935d2e3ee7ca124b47d9e2d483e7b2e4a92b07bd2d8766a9f22d3049e26c10ef"
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
    "top": "skid_buffer"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\synth.tcl",
      "sha256": "29b56e13814d1030c04d863ba09998c3a82280d9b54e4c748f929e915e8e32a2",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/skid_buffer.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing.xdc\"\r\nsynth_design -top skid_buffer -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-02/tier2_565ez3lf/skid_buffer_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\timing_io.tcl",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\power.rpt",
      "sha256": "1f45e8c0075c8d272cf48bac34700a236a17e49db9885c0d27bbd52144d43df0"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\timing.rpt",
      "sha256": "28fd4bcafa9ace7410c4d996ea453f80ef4544153f613a1864d0a09ec840cb72"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "20f7a22e53c0b4bf9e32c370470c497b9480a73bff549fe69f9d670ec9e52334"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\timing_routed.rpt",
      "sha256": "71da56dd6409d418e7e5c6f49aabc421e6254afe9e939b0fb5e51de85a5fb764"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\utilization.rpt",
      "sha256": "ac0208e0b5fff4efdd56c19b7a31061bc991a506fc496150e5ef449c4adca9df"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\utilization_routed.rpt",
      "sha256": "7c0d17015169b01595f2cebfdc28dd3041b53f313970100d366e4b0b83585a19"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\iter_000\\skid_buffer.v",
      "sha256": "db2d6a1ef9ecc8d6d5d06b2aee4c89fbb212d584c79ac82d12001cb969b2438d"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-02\\tier2_565ez3lf\\skid_buffer_build\\inputs\\testbench_path.v",
    "sha256": "935d2e3ee7ca124b47d9e2d483e7b2e4a92b07bd2d8766a9f22d3049e26c10ef"
  },
  "testbench_top": "skid_buffer_tb",
  "top_module": "skid_buffer"
}
```
