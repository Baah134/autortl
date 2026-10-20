
set_part xc7a35tcpg236-1
read_verilog "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/mux4.v"
set fp [open "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/timing.xdc" w]
puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/timing.xdc"
synth_design -top mux4 -flatten_hierarchy rebuilt 
set fp [open "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/timing_io.tcl" w]
puts $fp {set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]}
puts $fp {if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}}
puts $fp {if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}}
close $fp
source "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/timing_io.tcl"
report_utilization -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/utilization.rpt"
report_timing_summary -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/timing.rpt"
opt_design
place_design
phys_opt_design -hold_fix
route_design
report_utilization -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/utilization_routed.rpt"
report_timing_summary -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/timing_routed.rpt"
report_design_analysis -logic_level_distribution -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/design_analysis.rpt"
report_power -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/power.rpt"
catch { report_methodology -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/methodology.rpt" }
catch { report_qor_suggestions -file "C:/Users/prince.baah/Downloads/autortl-work/logs/physical-hold-fix-01/qor_suggestions.rpt" }
puts "SYNTH_COMPLETE"
