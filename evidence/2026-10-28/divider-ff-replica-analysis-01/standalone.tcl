set_part xc7a35tcpg236-1
read_verilog [list "C:/Users/prince.baah/Downloads/autortl-work/evidence/2026-10-23/generated-divider-attempt-01/build-golden-divider-01/iterative_divider_best.v" "C:/Users/prince.baah/Downloads/autortl-work/evidence/2026-10-23/generated-divider-attempt-01/build-golden-divider-01/modules/iterative_divider_core/iterative_divider_core.v"]
set fp [open "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/div_standalone/timing.xdc" w]
puts $fp {create_clock -period 10.000 -name clk [get_ports clk]}
close $fp
read_xdc "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/div_standalone/timing.xdc"
synth_design -top iterative_divider -flatten_hierarchy rebuilt
set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs
set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]
opt_design
place_design
route_design
report_utilization -file "C:/Users/prince.baah/AppData/Local/Temp/claude/C--Users-prince-baah-Downloads-autortl-work/55d6b518-5dad-43c2-b889-516d22ebd733/scratchpad/div_standalone/util.rpt"
set ffs [lsort [get_cells -hierarchical -filter {REF_NAME =~ FD*}]]
puts "FFCOUNT [llength $ffs]"
foreach c $ffs { puts "FF $c" }
