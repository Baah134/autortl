catch {close_project -quiet}
create_project -in_memory -part xc7a35tcpg236-1
read_verilog {C:/Users/prince.baah/Downloads/autortl-work/evidence/2026-10-23/generated-divider-attempt-01/build-golden-divider-01/iterative_divider_best.v}
set fp [open "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/iterative_divider/ooc/p3.050/timing.xdc" w]
puts $fp {create_clock -period 3.050 -name clk [get_ports clk]}
puts $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/iterative_divider/ooc/p3.050/timing.xdc"
synth_design -top iterative_divider -flatten_hierarchy rebuilt -mode out_of_context
opt_design
place_design
route_design
report_timing_summary -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/iterative_divider/ooc/p3.050/timing_routed.rpt"
report_timing -max_paths 1 -nworst 1 -path_type full -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/iterative_divider/ooc/p3.050/critical_path.rpt"
report_utilization -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/iterative_divider/ooc/p3.050/utilization_routed.rpt"
puts "FMAX_ATTEMPT_DONE"
