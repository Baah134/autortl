# Basys 3 build of the echo whose transmitter the harness generated.
#   vivado -mode batch -source build.tcl -tclargs <out dir> <harness .v> [<harness .v> ...]
# The harness files (its winning top, plus any frozen child it instantiates)
# are read unchanged; the board logic around them is hand-written.
if {[llength $argv] < 2} { error "usage: -tclargs <out dir> <harness .v> \[<harness .v> ...\]" }
set out [lindex $argv 0]
set harness [lrange $argv 1 end]
set board [file normalize [file join [file dirname [info script]] ..]]
set hw    [file normalize [file join $board .. .. ..]]
file mkdir $out

read_verilog [concat [list $hw/uart_echo/rtl/uart_rx.v $hw/harness_winners/rtl/shell_fifo.v] \
                     $harness [list $board/rtl/basys3_harness_uart_tx.v]]
read_xdc $board/constraints/basys3_harness_uart_tx.xdc

synth_design -top basys3_harness_uart_tx -part xc7a35tcpg236-1
opt_design
place_design
route_design

report_timing_summary -file $out/timing_summary.rpt
report_utilization    -file $out/utilization.rpt
report_utilization -cells [get_cells u_harness_tx] -file $out/harness_tx_utilization.rpt
report_drc            -file $out/drc.rpt

set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold  -max_paths 1]]
puts "RESULT: WNS=$wns ns WHS=$whs ns"
if {$wns < 0 || $whs < 0} { error "Timing not met" }

write_bitstream -force $out/basys3_harness_uart_tx.bit
puts "RESULT: bitstream $out/basys3_harness_uart_tx.bit"
