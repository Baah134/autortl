catch {close_project -quiet}
create_project -in_memory -part xc7a35tcpg236-1
read_verilog {C:/Users/prince.baah/Downloads/autortl-work/evidence/2026-10-22/generated-fifo-attempt-05/build-golden-fifo-05/sync_fifo_best.v}
set fp [open "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/sync_fifo/harness/p9.850/timing.xdc" w]
puts $fp {create_clock -period 9.850 -name clk [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/sync_fifo/harness/p9.850/timing.xdc"
synth_design -top sync_fifo -flatten_hierarchy rebuilt 
set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}
if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}
opt_design
place_design
route_design
report_timing_summary -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/sync_fifo/harness/p9.850/timing_routed.rpt"
report_timing -max_paths 1 -nworst 1 -path_type full -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/sync_fifo/harness/p9.850/critical_path.rpt"
report_utilization -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/fmax_run/sync_fifo/harness/p9.850/utilization_routed.rpt"
puts "FMAX_ATTEMPT_DONE"
