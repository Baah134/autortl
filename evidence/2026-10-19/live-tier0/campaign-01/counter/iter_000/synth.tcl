set_msg_config -id {Synth 8-327} -new_severity ERROR
set_msg_config -id {Synth 8-3352} -new_severity ERROR
set_part xc7a35tcpg236-1
read_verilog "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/counter.v"
set fp [open "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/timing.xdc" w]
puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/timing.xdc"
synth_design -top counter -flatten_hierarchy rebuilt 
report_utilization -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/utilization.rpt"
report_timing_summary -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/timing.rpt"
opt_design
place_design

route_design
report_utilization -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/utilization_routed.rpt"
report_timing_summary -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/timing_routed.rpt"
report_design_analysis -logic_level_distribution -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/design_analysis.rpt"
report_power -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/power.rpt"
catch { report_methodology -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/methodology.rpt" }
catch { report_qor_suggestions -file "C:/Users/prince.baah/Downloads/autortl-work/logs/curriculum/tier0_t2_rkf80/counter/iter_000/qor_suggestions.rpt" }
puts "SYNTH_COMPLETE"
