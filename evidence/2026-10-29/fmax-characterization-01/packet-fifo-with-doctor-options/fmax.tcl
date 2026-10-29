catch {close_project -quiet}
create_project -in_memory -part xc7a35tcpg236-1
read_verilog {C:/Users/prince.baah/Downloads/autortl-work/evidence/2026-10-22/generated-packet-attempt-01/build-golden-packet-01/packet_fifo_best.v}
set fp [open "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/packet_doctor_knobs/both/timing.xdc" w]
puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/packet_doctor_knobs/both/timing.xdc"
synth_design -top packet_fifo -flatten_hierarchy rebuilt -retiming 
set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}
if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/packet_doctor_knobs/both/timing_routed.rpt"
report_timing -max_paths 1 -nworst 1 -path_type full -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/packet_doctor_knobs/both/critical_path.rpt"
report_utilization -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/packet_doctor_knobs/both/utilization_routed.rpt"
puts "FMAX_ATTEMPT_DONE"
