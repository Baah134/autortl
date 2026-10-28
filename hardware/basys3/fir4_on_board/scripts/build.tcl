# Non-project synthesis, implementation and bitstream for the FIR4 shell.
# Run from this folder:  vivado -mode batch -source scripts/build.tcl
set root [file normalize [file join [file dirname [info script]] ..]]
set uart [file normalize [file join $root .. uart_echo rtl]]
set out  $root/build
file mkdir $out

read_verilog [list \
    $uart/uart_rx.v \
    $uart/uart_tx.v \
    $uart/sync_fifo.v \
    $root/dut/signed_fir4.v \
    $root/rtl/basys3_fir4_shell.v]
read_xdc $root/constraints/basys3_fir4_shell.xdc

synth_design -top basys3_fir4_shell -part xc7a35tcpg236-1
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
if {$wns < 0 || $whs < 0} {
    error "Timing not met"
}

write_bitstream -force $out/basys3_fir4_shell.bit
puts "RESULT: bitstream $out/basys3_fir4_shell.bit"
