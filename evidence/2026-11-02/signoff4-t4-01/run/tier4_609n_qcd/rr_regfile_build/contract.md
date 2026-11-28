# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (rr_arbiter4, regfile8x8) and the top rr_regfile, children first and top last; no frozen companion is compiled beside it. Only the top rr_regfile carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define rr_regfile. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

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
    "dynamic_power_w": 0.06,
    "ff_pct": 0.21634615384615385,
    "ff_total": 41600,
    "ff_used": 90,
    "lut_pct": 0.19230769230769232,
    "lut_total": 20800,
    "lut_used": 40,
    "reg2reg_wns_ns": 5.39,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.13,
    "whs_ns": 0.086,
    "wns_ns": 0.456
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\design_spec.json",
    "resolved_spec": {
      "connections": [
        {
          "dst_module": "regfile8x8",
          "dst_port": "wr_en",
          "src_module": "rr_arbiter4",
          "src_port": "wr_en"
        },
        {
          "dst_module": "regfile8x8",
          "dst_port": "wr_addr",
          "src_module": "rr_arbiter4",
          "src_port": "wr_addr"
        },
        {
          "dst_module": "regfile8x8",
          "dst_port": "wr_data",
          "src_module": "rr_arbiter4",
          "src_port": "wr_data"
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
          "name": "req",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 4
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "addr0",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 3
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "data0",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "addr1",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 3
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "data1",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "addr2",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 3
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "data2",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "addr3",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 3
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "data3",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "rd_addr",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 3
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "grant",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 4
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rd_data",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 8
        }
      ],
      "modules": [
        {
          "behavior": "Four-requester round-robin arbiter with a registered register-file write port. State last is the index 0..3 of the most recently granted requester; its reset value is 3, so requester 0 has the highest priority after reset. At each rising clk edge with rst low, using req and the addrN/dataN inputs sampled before the edge, search requesters in the order (last+1)%4, (last+2)%4, (last+3)%4, last and choose the first i with req[i] = 1 as the winner. If a winner exists: grant = 1 << winner (one-hot), wr_en = 1, wr_addr = addr<winner>, wr_data = data<winner>, last = winner. If req == 0: grant = 0, wr_en = 0, wr_addr = 0, wr_data = 0 and last is unchanged. grant, wr_en, wr_addr and wr_data are registers: they change only at rising edges and hold between edges whatever the inputs do. Synchronous active-high rst at a rising edge sets grant = 0, wr_en = 0, wr_addr = 0, wr_data = 0 and last = 3; reset has no effect between edges. Consequences: with all four requesting, grants rotate 0,1,2,3,0,...; a requester that keeps requesting is granted within 4 edges; a lone requester is granted at every edge. Python oracle: cycle-level model, one step per rising edge; keep last in state and return grant, wr_en, wr_addr and wr_data as registered by that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "grant": 1,
                "wr_addr": 1,
                "wr_data": 16,
                "wr_en": 1
              },
              "inputs": {
                "addr0": 1,
                "addr1": 2,
                "addr2": 3,
                "addr3": 4,
                "data0": 16,
                "data1": 32,
                "data2": 48,
                "data3": 64,
                "req": 15,
                "rst": 0
              }
            },
            {
              "after_cycles": 4,
              "expected": {
                "grant": 8,
                "wr_addr": 4,
                "wr_data": 64,
                "wr_en": 1
              },
              "inputs": {
                "addr0": 1,
                "addr1": 2,
                "addr2": 3,
                "addr3": 4,
                "data0": 16,
                "data1": 32,
                "data2": 48,
                "data3": 64,
                "req": 15,
                "rst": 0
              }
            },
            {
              "after_cycles": 3,
              "expected": {
                "grant": 2,
                "wr_addr": 2,
                "wr_data": 32,
                "wr_en": 1
              },
              "inputs": {
                "addr0": 1,
                "addr1": 2,
                "addr2": 3,
                "addr3": 4,
                "data0": 16,
                "data1": 32,
                "data2": 48,
                "data3": 64,
                "req": 10,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rr_arbiter4",
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
              "name": "req",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "addr0",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "data0",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "addr1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "data1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "addr2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "data2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "addr3",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "data3",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "grant",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_en",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_addr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "wr_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
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
          "behavior": "8-entry by 8-bit register file with one synchronous write port and one registered read port, read-before-write. At each rising clk edge with rst low: rd_data takes mem[rd_addr] as it was BEFORE this edge's write (read-first: reading the address written at the same edge returns the old value; the new value is visible to a read sampled at the next edge); then, if wr_en = 1, mem[wr_addr] = wr_data. wr_addr and wr_data are ignored when wr_en = 0. rd_data is a register and holds between edges. Synchronous active-high rst at a rising edge clears all 8 entries and rd_data to 0 and blocks any write at that edge; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the 8 entries in state and return rd_data as registered by that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state (all entries zero) and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "rd_data": 0
              },
              "inputs": {
                "rd_addr": 5,
                "rst": 0,
                "wr_addr": 5,
                "wr_data": 165,
                "wr_en": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "rd_data": 165
              },
              "inputs": {
                "rd_addr": 5,
                "rst": 0,
                "wr_addr": 5,
                "wr_data": 165,
                "wr_en": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "rd_data": 0
              },
              "inputs": {
                "rd_addr": 3,
                "rst": 0,
                "wr_addr": 3,
                "wr_data": 255,
                "wr_en": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "regfile8x8",
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
              "name": "wr_en",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wr_addr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wr_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rd_addr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rd_data",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
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
      "top_name": "rr_regfile"
    },
    "sha256": "4138d30db9e69af8f74ad67241765bffb736efb26b2e92b340113ef92a682c15",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\rr_regfile.v",
    "source_sha256": "c993eaf6fc8dd393e00b9b552c0c37334dd7cf896a15597aca4d0198340a22fa"
  },
  "edit_scope": {
    "children": [
      "rr_arbiter4",
      "regfile8x8"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top rr_regfile and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [],
    "top": "rr_regfile"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\inputs\\testbench_path.v",
      "sha256": "e71840495db4324b9a11e09cba164c682f97f92477679f8daf1ed0819ba50a0a"
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
    "top": "rr_regfile"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\synth.tcl",
      "sha256": "011d1e0f56f7b909ff9a46d73b9de6829c7f19af93164abdb637f03dcc799f0c",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/rr_regfile.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing.xdc\"\r\nsynth_design -top rr_regfile -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t4-01/tier4_609n_qcd/rr_regfile_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\timing_io.tcl",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\power.rpt",
      "sha256": "10846ced5a31a30a09bedf043c6cc268bc176ea419902f227fa65c309141b10c"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\timing.rpt",
      "sha256": "13c895709381c2647743794ee14c465cad6a9228618a6a76887d790e5b958f18"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "e6720658b9ba95c1a36296ef1606b903ecfdbfdd9f68fc62ff6d69dd93e480e7"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\timing_routed.rpt",
      "sha256": "4a686665fefbc8540782f35dd3360522d65f390859a2f9e0abc41ef4f978a25c"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\utilization.rpt",
      "sha256": "7bf9ef2ac0af86e59a6d852e15345ffdade3fa76c4cac11a96d6b85209bb49a3"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\utilization_routed.rpt",
      "sha256": "cb57713336c10cbf1e17b5c209e8efc06fbd5c3fe0f999dd36f43432add6f6ba"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\iter_000\\rr_regfile.v",
      "sha256": "c993eaf6fc8dd393e00b9b552c0c37334dd7cf896a15597aca4d0198340a22fa"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t4-01\\tier4_609n_qcd\\rr_regfile_build\\inputs\\testbench_path.v",
    "sha256": "e71840495db4324b9a11e09cba164c682f97f92477679f8daf1ed0819ba50a0a"
  },
  "testbench_top": "rr_regfile_tb",
  "top_module": "rr_regfile"
}
```
