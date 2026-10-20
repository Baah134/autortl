# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

Preserve the frozen source's ports, names, directions, widths, parameters and parameter defaults. Preserve reset polarity, synchronous/asynchronous behavior, priority, state initialization and every observable cycle of latency, throughput, flags and handshakes, including disabled cycles. Preserve supported parameter behavior and high-bit semantics. No new pipeline stages, extra clock cycles, interfaces or invented thresholds. For build mode, the integrated design remains subject to its module specs.

## Verification gates

Use the frozen testbench unchanged. Pass static/interface and declared latency checks, xvlog compilation, xelab elaboration and xsim -runall. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for promotion. Missing or unknown evidence is not success.

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
    "dynamic_power_w": 0.053,
    "ff_pct": 0.0889423076923077,
    "ff_total": 41600,
    "ff_used": 37,
    "lut_pct": 0.2644230769230769,
    "lut_total": 20800,
    "lut_used": 55,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.123,
    "whs_ns": 0.113,
    "wns_ns": 0.494
  },
  "clock_period_ns": 10.0,
  "execution_context": {
    "dependencies": [],
    "part": "xc7a35tcpg236-1",
    "period_ns": 10.0,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR"
    },
    "synthesis_template": "c9d0bf78e20ec5b5854a3e48a12cb9d6ce15be79e660b27b3bf703670a77197a",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\inputs\\testbench_path.v",
      "sha256": "b4b51f80d1bc94dc63acae16c8b4080bc0277a6342268c900ffb18fed09391f3"
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
    "top": "counter"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\synth.tcl",
      "sha256": "582484ead775b56cb4e3eef50b6c3ca770c900589206d3ed6846d13eff91dcff",
      "text": "set_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/counter.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/timing.xdc\"\r\nsynth_design -top counter -flatten_hierarchy rebuilt \r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/timing_io.tcl\" w]\r\nputs $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}\r\nputs $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}\r\nputs $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}\r\nclose $fp\r\nsource \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/timing_io.tcl\"\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/timing_routed.rpt\"\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/contract-campaign-03/tier0_c05h57lo/counter/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\timing.xdc",
      "sha256": "fa142c09f0fadb5e303ca9fea08c02bc353451533e44aeee9cd9a0231cc8bede",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\timing_io.tcl",
      "sha256": "6b38098841a48bbb3ab15de49d2bf2baf7e4384f599259ff5f3afa2c2b1daf00",
      "text": "set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]\r\nif {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}\r\nif {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}\r\n",
      "truncated": false
    }
  ],
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\power.rpt",
      "sha256": "fd1d5f629465679df1b10be2cc34bfea7450ad385ad796b0a459cb9474d822e6"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\timing.rpt",
      "sha256": "272c2a49ef73e8a350e711612e18cf02e57b28d489a46158bef072b989dce1f5"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\timing_routed.rpt",
      "sha256": "b8550cf9a8b3e887a31e1ca4b9f47786a2f39baf9b05cbf78b0f539d29b0b3dd"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\utilization.rpt",
      "sha256": "f63c80d8b339e4abb8350527832593fb1b746bed98c8b017451945ae84d8236e"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\utilization_routed.rpt",
      "sha256": "9f71685339a19a43d1b8e3432c4cc788551c016f9b8f9b177bb2ee4d0420c15a"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\iter_000\\counter.v",
      "sha256": "515edd5171ffd158ae64780cae4a474637bd9ea1fe248099dac6b49ae55f2d06"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\contract-campaign-03\\tier0_c05h57lo\\counter\\inputs\\testbench_path.v",
    "sha256": "b4b51f80d1bc94dc63acae16c8b4080bc0277a6342268c900ffb18fed09391f3"
  },
  "testbench_top": "counter_tb",
  "top_module": "counter"
}
```
