# Basys 3 build of the echo whose receiver and transmitter the harness generated.
#   vivado -mode batch -source build.tcl -tclargs <out dir> <rx winner .v> <tx winner .v>
# The two winner files are read unchanged; only the wrapper is hand-written.
if {[llength $argv] != 3} { error "usage: -tclargs <out dir> <rx winner .v> <tx winner .v>" }
set out [lindex $argv 0]
set rx_winner [file normalize [lindex $argv 1]]
set tx_winner [file normalize [lindex $argv 2]]
set board [file normalize [file join [file dirname [info script]] ..]]
file mkdir $out

read_verilog [list $rx_winner $tx_winner $board/rtl/basys3_harness_echo.v]
read_xdc $board/constraints/basys3_harness_echo.xdc

synth_design -top basys3_harness_echo -part xc7a35tcpg236-1
opt_design
place_design
route_design

report_timing_summary -file $out/timing_summary.rpt
report_utilization    -file $out/utilization.rpt
report_utilization -hierarchical -file $out/utilization_hier.rpt
report_drc            -file $out/drc.rpt

set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold  -max_paths 1]]
puts "RESULT: WNS=$wns ns WHS=$whs ns"
if {$wns < 0 || $whs < 0} { error "Timing not met" }

write_bitstream -force $out/basys3_harness_echo.bit
puts "RESULT: bitstream $out/basys3_harness_echo.bit"
