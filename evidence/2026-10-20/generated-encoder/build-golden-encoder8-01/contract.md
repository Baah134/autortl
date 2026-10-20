# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

Preserve the frozen source's ports, names, directions, widths, parameters and parameter defaults. Preserve reset polarity, synchronous/asynchronous behavior, priority, state initialization and every observable cycle of latency, throughput, flags and handshakes, including disabled cycles. Preserve supported parameter behavior and high-bit semantics. No new pipeline stages, extra clock cycles, interfaces or invented thresholds. For build mode, the integrated design remains subject to its module specs.

## Verification gates

Use the frozen testbench unchanged. Pass static/interface and declared latency checks when a numeric declaration is known, xvlog compilation, xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, not zero; an annotation alone is not independent behavioral proof. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for promotion. Missing or unknown evidence is not success.

## Objective and completion

Objective minimize_luts maps to lut_used: require strictly lower than the previous verified best, under the same device, clock and constraints. No minimum percentage gain or extra slack margin is imposed. Final evaluator ACCEPT with zero failed criteria and all deterministic promotion gates are required. DONE describes a completed experiment; best_iteration 0 retains the baseline and claims no accepted improvement. Only a promoted best_iteration > 0 establishes an accepted gain.

## Fixed measurement authority

The JSON below records source/testbench identities, actual device, clock, tool context, constraints and retained report hashes. Numeric metrics are the parsed structured evidence, with routed reports preferred. The candidate's retained synthesis script records actual permitted retiming or physical optimization settings; these never change behavioral obligations.

```json
{
  "baseline_metrics": {
    "bram_total": 50.0,
    "bram_used": 0.0,
    "dsp_total": 90,
    "dsp_used": 0,
    "dynamic_power_w": 0.011,
    "ff_pct": 0.009615384615384616,
    "ff_total": 41600,
    "ff_used": 4,
    "lut_pct": 0.028846153846153848,
    "lut_total": 20800,
    "lut_used": 6,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.081,
    "whs_ns": 0.009,
    "wns_ns": 0.528
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\priority_encoder8.v",
    "source_sha256": "e62e9b37985faa79f76389f9a9450b78274b72e7f294b8ddc64ad79af92ec704"
  },
  "execution_context": {
    "dependencies": [
      {
        "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\modules\\priority_encoder8_core\\priority_encoder8_core.v",
        "sha256": "c1eeea95647a9bcc614cee59dfc0a6648b2dab53a32aded3ad3a5b39ad86a59a"
      }
    ],
    "part": "xc7a35tcpg236-1",
    "period_ns": 10.0,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR"
    },
    "synthesis_template": "c9d0bf78e20ec5b5854a3e48a12cb9d6ce15be79e660b27b3bf703670a77197a",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\priority_encoder8_tb.v",
      "sha256": "6df8f44d22ec1d516ff704fac1f8d3233c96829a37f436e5ea198602cd95ac0f"
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
    "top": "priority_encoder8"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\synth.tcl",
      "sha256": "293e07ad1f030e5c20f943e6b67b939adc4bda98c5f658f0b9c84e80cda2f547",
      "text": "set_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/priority_encoder8.v\" \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/modules/priority_encoder8_core/priority_encoder8_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/timing.xdc\"\r\nsynth_design -top priority_encoder8 -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/timing_routed.rpt\"\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/build-golden-encoder8-01/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\power.rpt",
      "sha256": "d5d2f126a0d9d571d1cfb1332af8931892a09d0b2e335fe229934ef51807bd5f"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\timing.rpt",
      "sha256": "127be96c1cc1cf44743eff738d477aecea367d2f847f16ba9fcc16964926aa22"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\timing_routed.rpt",
      "sha256": "918cc1f3d4f83add2bc2bbf2e2daf0aa08a652fca8f13277da438c7ff9af4896"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\utilization.rpt",
      "sha256": "48a18788433b665a884e88802da87fa5cabd3f57d9f13f56ee4120c61bf728d8"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\utilization_routed.rpt",
      "sha256": "f66cfb6eb9bf43d1440b1bbfc451a8376800f2b79a6cc5cfd9ce04a48b78faff"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\iter_000\\priority_encoder8.v",
      "sha256": "e62e9b37985faa79f76389f9a9450b78274b72e7f294b8ddc64ad79af92ec704"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\modules\\priority_encoder8_core\\priority_encoder8_core.v",
      "sha256": "c1eeea95647a9bcc614cee59dfc0a6648b2dab53a32aded3ad3a5b39ad86a59a"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\build-golden-encoder8-01\\priority_encoder8_tb.v",
    "sha256": "6df8f44d22ec1d516ff704fac1f8d3233c96829a37f436e5ea198602cd95ac0f"
  },
  "testbench_top": "priority_encoder8_tb",
  "top_module": "priority_encoder8"
}
```
