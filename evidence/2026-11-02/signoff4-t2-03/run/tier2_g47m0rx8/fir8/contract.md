# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

Preserve the frozen source's ports, names, directions, widths, parameters and parameter defaults. Preserve reset polarity, synchronous/asynchronous behavior, priority, state initialization and every observable cycle of latency, throughput, flags and handshakes, including disabled cycles. Preserve supported parameter behavior and high-bit semantics. No new pipeline stages, extra clock cycles, interfaces or invented thresholds. Standalone optimization has no typed build spec exception: do not infer unspecified behavior merely from missing test coverage.

## Implementation flow

Mode out_of_context, fixed by the harness. Out-of-context implementation (chip_top_flow_for_soc_block): the top is a block inside a larger design, synthesized with synth_design -mode out_of_context and placed and routed without I/O buffers or package pins. clk is constrained at the target period and modeled as driven by a global clock buffer (HD.CLK_SRC). Data ports have no input or output delay and no pad delay, so they are unconstrained I/O; the routed WNS and WHS, and timing acceptance, cover the internal clocked paths only, and combinational logic between a port and its first or last register is not timed. Utilization excludes I/O buffers.

## Verification gates

The current top has known numeric latency 1; require a matching // @latency 1 annotation. Preserve its defined cycle behavior. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

Use the frozen testbench unchanged. Pass static/interface and declared latency checks when a numeric declaration is known, xvlog compilation, xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, not zero; an annotation alone is not independent behavioral proof. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for timing closure and for promotion, except timing_progress below. Missing or unknown evidence is not success.

## Objective and completion

First establish timing feasibility: the candidate must pass simulation and all verification/metric/receipt gates, with timing_met=true, WNS >= 0 and WHS >= 0. A candidate meeting those gates may replace a previous verified best whose known consistent timing evidence fails setup or hold, even when area or power increases or stays equal. Classify this as timing_recovery: a feasibility recovery, not resource or power savings. Unknown, missing or contradictory timing evidence does not establish a timing recovery. While the previous best is still timing-infeasible, a verified candidate that is also infeasible may replace it only with strictly better setup WNS and hold WHS not worse beyond a small tolerance. Classify this as timing_progress: progress toward closure, not closure; a timing-feasible candidate always outranks it, a feasible previous best is never replaced by an infeasible candidate, and a run whose best is still infeasible has not closed timing. Once both designs are timing-feasible, objective maximize_freq maps to reg2reg_wns_ns (register-to-register setup slack) when both designs report a finite value, otherwise wns_ns for both, never mixed: require strictly higher at the same clock period than the previous verified best, under the same device, clock and constraints. No minimum percentage gain or extra slack margin is imposed. Final evaluator ACCEPT with zero failed criteria and all deterministic promotion gates are required. DONE describes a completed experiment; best_iteration 0 retains the baseline and claims no accepted improvement. Only a promoted best_iteration > 0 establishes an accepted improvement; its recorded kind distinguishes timing recovery and timing progress from objective gain.

## Fixed measurement authority

The JSON below records source/testbench identities, actual device, clock, tool context, constraints and retained report hashes. Numeric metrics are the parsed structured evidence, with routed reports preferred. The candidate's retained synthesis script records actual permitted retiming or physical optimization settings; these never change behavioral obligations.

```json
{
  "baseline_metrics": {
    "bram_total": 50.0,
    "bram_used": 0.0,
    "dsp_total": 90,
    "dsp_used": 6,
    "dynamic_power_w": 0.012,
    "ff_pct": 0.3076923076923077,
    "ff_total": 41600,
    "ff_used": 128,
    "lut_pct": 0.4855769230769231,
    "lut_total": 20800,
    "lut_used": 101,
    "reg2reg_wns_ns": -9.981,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 0.081,
    "whs_ns": 0.171,
    "wns_ns": -9.981
  },
  "build_spec": null,
  "clock_period_ns": 6.666666666666667,
  "declared_latency": {
    "cycles": 1,
    "known": true,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\fir8.v",
    "source_sha256": "6891b237208b24bea75aebc16a306f3b7bc51542022dab3e740a38bbe56d880e"
  },
  "execution_context": {
    "dependencies": [],
    "implementation": "out_of_context",
    "part": "xc7a35tcpg236-1",
    "period_ns": 6.666666666666667,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR",
      "Synth 8-9873": "ERROR",
      "VRFC 10-3609": "ERROR"
    },
    "synthesis_template": "61e44d95134130552d86e050a4db65035952d348028dc942b327b8aced90b3d1",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\inputs\\testbench_path.v",
      "sha256": "67218f24c3c1f2b130b4c714ed18cd4efbfe9f9e28e8f71592f2defea22f069b"
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
    "top": "fir8"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\synth.tcl",
      "sha256": "438bcb419250acca4071eb5c44522245f4df5003cb48c93a854a0ba3f0cb9cca",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/fir8.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 6.667 -name clk [get_ports clk]}\r\nputs $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/timing.xdc\"\r\nsynth_design -top fir8 -flatten_hierarchy rebuilt -mode out_of_context \r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/signoff4-t2-03/tier2_g47m0rx8/fir8/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\timing.xdc",
      "sha256": "952d85aec49f6e20f2003112943b665b86d078d91c18438bd81498e37ec1a892",
      "text": "create_clock -period 6.667 -name clk [get_ports clk]\r\nset_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]\r\n",
      "truncated": false
    }
  ],
  "implementation": {
    "meaning": "Out-of-context implementation (chip_top_flow_for_soc_block): the top is a block inside a larger design, synthesized with synth_design -mode out_of_context and placed and routed without I/O buffers or package pins. clk is constrained at the target period and modeled as driven by a global clock buffer (HD.CLK_SRC). Data ports have no input or output delay and no pad delay, so they are unconstrained I/O; the routed WNS and WHS, and timing acceptance, cover the internal clocked paths only, and combinational logic between a port and its first or last register is not timed. Utilization excludes I/O buffers.",
    "mode": "out_of_context"
  },
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\power.rpt",
      "sha256": "4091ec3bf0afea58847ad073f13114492452b4fa053a2d029323cd03d12f4a55"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\timing.rpt",
      "sha256": "19aa9fa5bfa5aebedf19129c01f463796f044184e85c6bf5144b14dd3b84f1e3"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\timing_reg2reg.rpt",
      "sha256": "b6a587de5d50e262781d155c5328801cb8088c58c7ab1d12e8d9bbca486564ed"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\timing_routed.rpt",
      "sha256": "3e87f9e974d8a3ab55c21dfa6a71d760c3051f42e039f4bd0c2c1b3e8fab1ffa"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\utilization.rpt",
      "sha256": "8d1c2945afb9ce30fbf4fda33b0cbec4f36dfbc712b4f9338c2a565a1999af67"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\utilization_routed.rpt",
      "sha256": "884858b85b88de69b7067209cceef8665c534fd28501cb51bd2e8dc3cbb2e5bb"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\iter_000\\fir8.v",
      "sha256": "6891b237208b24bea75aebc16a306f3b7bc51542022dab3e740a38bbe56d880e"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\signoff4-t2-03\\tier2_g47m0rx8\\fir8\\inputs\\testbench_path.v",
    "sha256": "67218f24c3c1f2b130b4c714ed18cd4efbfe9f9e28e8f71592f2defea22f069b"
  },
  "testbench_top": "fir8_tb",
  "top_module": "fir8"
}
```
