create_clock -period 10.000 -name clk [get_ports clk]
set data_inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
if {[llength $data_inputs] > 0} {set_input_delay -clock clk -max 0.000 $data_inputs; set_input_delay -clock clk -min 0.000 $data_inputs}
if {[llength [all_outputs]] > 0} {set_output_delay -clock clk -max 0.000 [all_outputs]; set_output_delay -clock clk -min 0.000 [all_outputs]}
