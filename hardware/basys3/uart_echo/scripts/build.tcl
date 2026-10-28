# Non-project synthesis, implementation and bitstream for the Basys 3 echo.
# Run from anywhere:  vivado -mode batch -source scripts/build.tcl
set root [file normalize [file join [file dirname [info script]] ..]]
set out  $root/build
file mkdir $out

read_verilog [list \
    $root/rtl/uart_rx.v \
    $root/rtl/uart_tx.v \
    $root/rtl/sync_fifo.v \
    $root/rtl/basys3_uart_echo.v]
read_xdc $root/constraints/basys3_uart_echo.xdc

synth_design -top basys3_uart_echo -part xc7a35tcpg236-1
opt_design
place_design
route_design

report_timing_summary -file $out/timing_summary.rpt
report_utilization    -file $out/utilization.rpt
report_drc            -file $out/drc.rpt

set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold  -max_paths 1]]
puts "RESULT: WNS=$wns ns WHS=$whs ns"
if {$wns < 0 || $whs < 0} {
    error "Timing not met"
}

write_bitstream -force $out/basys3_uart_echo.bit
puts "RESULT: bitstream $out/basys3_uart_echo.bit"
