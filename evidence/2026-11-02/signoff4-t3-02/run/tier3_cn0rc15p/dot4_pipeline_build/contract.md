# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (dot4_pair01, dot4_pair23, dot4_merge) and the top dot4_pipeline, children first and top last; no frozen companion is compiled beside it. Only the top dot4_pipeline carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define dot4_pipeline; modules the trusted testbench instantiates directly (dot4_merge) must stay defined and be live-reached from dot4_pipeline. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

## Implementation flow

Mode chip_top, fixed by the harness. Chip-top implementation: the top is the whole FPGA design. Every port bit gets an I/O buffer on a package pin, and data ports have zero input and output delay to clk, so the routed WNS and WHS include pad delay. Utilization includes the I/O buffers.

## Verification gates

The current top's numeric latency is UNKNOWN, not zero. Its missing @latency annotation is neither FAIL nor INVESTIGATE and must not block ACCEPT. Do not invent a numeric top annotation from child typed-module metadata or an arbitrary aggregate wrapper. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "dynamic_power_w": 0.087,
    "ff_pct": 0.125,
    "ff_total": 41600,
    "ff_used": 52,
    "lut_pct": 1.5625,
    "lut_total": 20800,
    "lut_used": 325,
    "reg2reg_wns_ns": 7.022,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.157,
    "whs_ns": 0.202,
    "wns_ns": 0.087
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\design_spec.json",
    "resolved_spec": {
      "connections": [
        {
          "dst_module": "dot4_merge",
          "dst_port": "left_sum",
          "src_module": "dot4_pair01",
          "src_port": "pair01_sum"
        },
        {
          "dst_module": "dot4_merge",
          "dst_port": "right_sum",
          "src_module": "dot4_pair23",
          "src_port": "pair23_sum"
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
          "direction": "output",
          "name": "dot_result",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 18
        }
      ],
      "modules": [
        {
          "behavior": "At each rising clk edge synchronous active-high rst sets pair01_sum=0. Otherwise register the unsigned exact sum a0*b0 + a1*b1, range 0..130050, without truncating product or addition carry. Each operand is independently unsigned 8-bit including 128..255. Outputs hold between rising edges, including during off-edge reset pulses. Throughput one input sample per edge. Python oracle returns arithmetic result for the current sample; the driver supplies latency, do not add a pipeline queue.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "pair01_sum": 130050
              },
              "inputs": {
                "a0": 255,
                "a1": 255,
                "b0": 255,
                "b1": 255,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "dot4_pair01",
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
              "direction": "output",
              "name": "pair01_sum",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 17
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
          "behavior": "At each rising clk edge synchronous active-high rst sets pair23_sum=0. Otherwise register the unsigned exact sum a2*b2 + a3*b3, range 0..130050, without truncating product or addition carry. Each operand is independently unsigned 8-bit including 128..255. Outputs hold between rising edges, including during off-edge reset pulses. Throughput one input sample per edge. Python oracle returns arithmetic result for the current sample; the driver supplies latency, do not add a pipeline queue.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "pair23_sum": 130050
              },
              "inputs": {
                "a2": 255,
                "a3": 255,
                "b2": 255,
                "b3": 255,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "dot4_pair23",
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
              "direction": "output",
              "name": "pair23_sum",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 17
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
          "behavior": "At each rising clk edge synchronous active-high rst sets dot_result=0. Otherwise register the unsigned exact sum left_sum + right_sum, each independent unsigned 17-bit input 0..131071; output range 0..262142, including combinations not reachable from the pair modules. Zero-extend operands before addition; preserve the carry. Output holds between edges, including off-edge reset pulses. Throughput one input sample per edge. Python oracle returns current arithmetic result; driver supplies latency, do not queue samples.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "dot_result": 262142
              },
              "inputs": {
                "left_sum": 131071,
                "right_sum": 131071,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "dot_result": 65536
              },
              "inputs": {
                "left_sum": 65535,
                "right_sum": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "dot4_merge",
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
              "name": "left_sum",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 17
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "right_sum",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 17
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "dot_result",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 18
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
      "top_name": "dot4_pipeline"
    },
    "sha256": "0762df6c91af51c96fd791ead6cfe455a2d6afafee8507053c5e3e4e7816a9cd",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\dot4_pipeline.v",
    "source_sha256": "f5faa60bd304ebe0f1c22210b7bb652c51b017c1e3892287482ee1a58a09ec50"
  },
  "edit_scope": {
    "children": [
      "dot4_pair01",
      "dot4_pair23",
      "dot4_merge"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top dot4_pipeline and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [
      "dot4_merge"
    ],
    "top": "dot4_pipeline"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\inputs\\testbench_path.v",
      "sha256": "dc325ab3047fd761c9dc3ad3d5c57e86ec91f5840953d8f2379f648527525205"
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
    "top": "dot4_pipeline"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\synth.tcl",
      "sha256": "033b3ef9eea8f4419020c27f48a4af9437d36deab16c509cb4e45d6ef336b411",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/dot4_pipeline.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing.xdc\"\r\nsynth_design -top dot4_pipeline -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t3-02/tier3_cn0rc15p/dot4_pipeline_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\timing_io.tcl",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\power.rpt",
      "sha256": "17459a8345ccad49573c1711af70496da4204505d60d8375a6dbc0b3869774c4"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\timing.rpt",
      "sha256": "c36d928a3c7266c0d5ad6734ec0f374863f29f12d0605eadfd2a9b7322da6894"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "22b6cac5c9ac24f2b4383e166fb8ea3d00b1c3db1e31b4c48fb9c384997d180a"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\timing_routed.rpt",
      "sha256": "fac3cf976a1aa279f3cad2cf3a0a00b97a185135d4a312f46e366357e804456c"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\utilization.rpt",
      "sha256": "57d59248aefc5f79e8aa8b8b095b50cbc24bcb1bc714585de35ff91773574219"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\utilization_routed.rpt",
      "sha256": "390c533dddc026854893cde2b3841a73293b3486eaad65338dfe4c6c81b2114c"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\iter_000\\dot4_pipeline.v",
      "sha256": "f5faa60bd304ebe0f1c22210b7bb652c51b017c1e3892287482ee1a58a09ec50"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t3-02\\tier3_cn0rc15p\\dot4_pipeline_build\\inputs\\testbench_path.v",
    "sha256": "dc325ab3047fd761c9dc3ad3d5c57e86ec91f5840953d8f2379f648527525205"
  },
  "testbench_top": "dot4_pipeline_tb",
  "top_module": "dot4_pipeline"
}
```
