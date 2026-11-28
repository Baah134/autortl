set_msg_config -id {VRFC 10-3609} -new_severity ERROR
set_msg_config -id {Synth 8-9873} -new_severity ERROR
set_msg_config -id {Designutils 20-1307} -new_severity ERROR
set_msg_config -id {Synth 8-327} -new_severity ERROR
set_msg_config -id {Synth 8-3352} -new_severity ERROR
set_part xc7a35tcpg236-1
read_verilog "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/aes128_core.v"
set fp [open "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing.xdc" w]
puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}
puts $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing.xdc"
synth_design -top aes128_core -flatten_hierarchy rebuilt -mode out_of_context 
report_utilization -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/utilization.rpt"
report_timing_summary -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing.rpt"
opt_design
place_design

route_design
report_utilization -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/utilization_routed.rpt"
report_timing_summary -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing_routed.rpt"
catch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing_reg2reg.rpt" } }
report_design_analysis -logic_level_distribution -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/design_analysis.rpt"
report_power -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/power.rpt"
catch { report_methodology -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/methodology.rpt" }
catch { report_qor_suggestions -file "C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/qor_suggestions.rpt" }
puts "SYNTH_COMPLETE"
