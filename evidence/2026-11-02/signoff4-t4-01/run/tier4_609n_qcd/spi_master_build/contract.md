# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (spi_master_core) and the top spi_master, children first and top last; no frozen companion is compiled beside it. Only the top spi_master carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define spi_master; modules the trusted testbench instantiates directly (spi_master_core) must stay defined and be live-reached from spi_master. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

## Implementation flow

Mode chip_top, fixed by the harness. Chip-top implementation: the top is the whole FPGA design. Every port bit gets an I/O buffer on a package pin, and data ports have zero input and output delay to clk, so the routed WNS and WHS include pad delay. Utilization includes the I/O buffers.

## Verification gates

The current top has known numeric latency 33; require a matching // @latency 33 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

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
    "ff_pct": 0.07932692307692307,
    "ff_total": 41600,
    "ff_used": 33,
    "lut_pct": 0.10096153846153846,
    "lut_total": 20800,
    "lut_used": 21,
    "reg2reg_wns_ns": 5.241,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.085,
    "whs_ns": 0.136,
    "wns_ns": 0.342
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\design_spec.json",
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
          "name": "cmd_data",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "cmd_valid",
          "packed_dimensions": null,
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "cmd_ready",
          "packed_dimensions": null,
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rsp_data",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rsp_valid",
          "packed_dimensions": null,
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "rsp_ready",
          "packed_dimensions": null,
          "protocol": "valid_ready",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "sclk",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "mosi",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "miso",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "cs_n",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        }
      ],
      "modules": [
        {
          "behavior": "SPI master, mode 0 (CPOL=0, CPHA=0), 8-bit MSB-first full-duplex transfers, one outstanding command. Public parameter HALF_PERIOD=2 is the number of clk cycles per SCLK half period; supported domain integer 1..8. Preserve the actual HALF_PERIOD-dependent timing, not only the default. Let H = HALF_PERIOD. Idle bus (after reset and whenever no transfer is active, including while a response is held): cs_n = 1, sclk = 0, mosi = 0. cmd_ready = !busy && !rsp_valid, from registered state only (no combinational path from cmd_valid, rsp_ready or rst). A command is accepted at rising edge k when cmd_valid && cmd_ready before that edge and rst is low; cmd_data is captured then and later cmd_data/cmd_valid changes are ignored until the next acceptance. After edge k: busy, cs_n = 0, sclk = 0, mosi = cmd_data[7]. Counting from edge k, sclk toggles exactly at edges k + j*H for j = 1..16 and holds at every other edge. Odd j: sclk 0->1 (rising SCLK) and at that same clk edge the master samples miso (the value present before the edge) as received bit (j-1)/2, MSB first, so the first sample becomes rsp_data[7]; miso is ignored at every other edge. Even j < 16: sclk 1->0 and mosi changes to cmd_data[7 - j/2] at that edge; mosi changes only at falling SCLK edges, so each bit is stable for 2H cycles around its rising edge. At j = 16 (edge k + 16H): sclk = 0, cs_n = 1, mosi = 0, busy ends, rsp_data = the 8 received bits and rsp_valid = 1. rsp_valid and rsp_data stay stable until the edge where rsp_valid && rsp_ready, which clears rsp_valid; cmd_ready was 0 at that edge, so the next command is accepted at the following edge at the earliest. Minimum accepted-transfer age is 16H+1 cycles (latency 33 for the default H = 2); it is exact when rsp_ready is high. rsp_data is unspecified while rsp_valid = 0. Synchronous active-high rst at a rising edge aborts any transfer or held response (no response from it ever appears), returns the bus to idle and overrides acceptance. Reset has no effect between edges and outputs must not be gated combinationally by rst. All outputs change only at rising clk edges. Transaction-level examples hold miso constant for the whole transfer, so rsp_data is 0x00 or 0xFF; each example step is one accepted command and returns its eventual rsp_data together with the idle bus values sclk = 0, mosi = 0, cs_n = 1 that hold whenever a response is presented. The serial miso schedule is not a transaction payload, so the independent cycle-exact testbench (an SPI slave model) is the verification authority for this module.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "scoreboard",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "cs_n": 1,
                "mosi": 0,
                "rsp_data": 255,
                "sclk": 0
              },
              "inputs": {
                "cmd_data": 165,
                "cmd_valid": 1,
                "miso": 1,
                "rsp_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "cs_n": 1,
                "mosi": 0,
                "rsp_data": 0,
                "sclk": 0
              },
              "inputs": {
                "cmd_data": 60,
                "cmd_valid": 1,
                "miso": 0,
                "rsp_ready": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "cs_n": 1,
                "mosi": 0,
                "rsp_data": 255,
                "sclk": 0
              },
              "inputs": {
                "cmd_data": 255,
                "cmd_valid": 1,
                "miso": 1,
                "rsp_ready": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 33,
          "latency_known": true,
          "name": "spi_master_core",
          "parameters": {
            "HALF_PERIOD": 2
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
              "name": "cmd_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "cmd_valid",
              "packed_dimensions": null,
              "protocol": "valid_ready",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "cmd_ready",
              "packed_dimensions": null,
              "protocol": "valid_ready",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rsp_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rsp_valid",
              "packed_dimensions": null,
              "protocol": "valid_ready",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rsp_ready",
              "packed_dimensions": null,
              "protocol": "valid_ready",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "sclk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "mosi",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "miso",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "cs_n",
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
      "top_name": "spi_master"
    },
    "sha256": "61c729ae322363a1fba7f2908b771dd3b587b0de920d999b34674dc1ce5b6a27",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": 33,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\spi_master.v",
    "source_sha256": "d86ad54db2b1c5c2130c63678d2ef56b82788d0c8cb620557935ef7811581084"
  },
  "edit_scope": {
    "children": [
      "spi_master_core"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top spi_master and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [
      "spi_master_core"
    ],
    "top": "spi_master"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\inputs\\testbench_path.v",
      "sha256": "267ebd00cf9a2c32320dd29632e1bb3db0a23d7fe95bd72afcadee37e73d73b9"
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
    "top": "spi_master"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\synth.tcl",
      "sha256": "c4e38ce77ec1d9d11132060f29248009d9e6949340a95f59feb71dc3862a38fe",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/spi_master.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing.xdc\"\r\nsynth_design -top spi_master -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/spi_master_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\timing_io.tcl",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\power.rpt",
      "sha256": "2ee64a88acbb23c57f4ef73776e5e66967ba22f2fa28d9496bc492fe73797fe0"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\timing.rpt",
      "sha256": "75e46a0533842635cd7bf7c833e8f30e4f431b273dd48413bf16a370aecac28d"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "8b6f5da9925e7d94b751b3d061d62d3ab5bfd3a38232fdb9896ae5c9b040c176"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\timing_routed.rpt",
      "sha256": "9a1cd637dae33d7a0aaca14a9bf89855a0748c90c373a06d1fe4bacb3a10ca02"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\utilization.rpt",
      "sha256": "054ff496a88e1db277d2a89e18d4393c66f10bc405612cf69ad9c26c4f8dd45b"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\utilization_routed.rpt",
      "sha256": "4a90ca38e3acc8db18d869afb1dadff5aac57d4843e6c8f146c6ab2d2677dbf4"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\iter_000\\spi_master.v",
      "sha256": "d86ad54db2b1c5c2130c63678d2ef56b82788d0c8cb620557935ef7811581084"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\spi_master_build\\inputs\\testbench_path.v",
    "sha256": "267ebd00cf9a2c32320dd29632e1bb3db0a23d7fe95bd72afcadee37e73d73b9"
  },
  "testbench_top": "spi_master_tb",
  "top_module": "spi_master"
}
```
