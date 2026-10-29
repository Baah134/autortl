# Non-project implementation and bitstream for stream_shell + one winner.
# Called by `python -m hwsuite build`:
#   vivado -mode batch -source build.tcl -tclargs <sources.txt> <out_dir> <in_bytes> <out_bytes>
# sources.txt lists absolute forward-slash paths, one per line.
if {[llength $argv] != 4} {
    error "usage: build.tcl <sources.txt> <out_dir> <in_bytes> <out_bytes>"
}
lassign $argv source_list out in_bytes out_bytes
foreach value [list $in_bytes $out_bytes] {
    if {![string is integer -strict $value] || $value < 1 || $value > 8} {
        error "byte widths must be integers 1..8"
    }
}
set root [file normalize [file join [file dirname [info script]] ..]]
file mkdir $out

set handle [open $source_list r]
set sources [split [string trim [read $handle]] "\n"]
close $handle
read_verilog $sources
read_xdc $root/constraints/stream_shell.xdc

synth_design -top stream_shell -part xc7a35tcpg236-1 \
    -generic IN_BYTES=$in_bytes -generic OUT_BYTES=$out_bytes
opt_design
place_design
route_design

report_timing_summary -file $out/timing_summary.rpt
report_utilization    -file $out/utilization.rpt
report_utilization -hierarchical -file $out/utilization_hier.rpt
report_drc            -file $out/drc.rpt

# The winner's own resources. The hierarchical table can omit small kept
# instances, so report the cell directly and fail if it does not exist.
set winner [get_cells -quiet u_dut/u_winner]
if {[llength $winner] != 1} {
    error "winner instance u_dut/u_winner not found in the routed design"
}
report_utilization -cells $winner -file $out/utilization_winner.rpt

set wns [get_property SLACK [get_timing_paths -setup -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -hold  -max_paths 1]]
puts "RESULT: WNS=$wns ns WHS=$whs ns"
if {$wns < 0 || $whs < 0} {
    error "Timing not met"
}
write_bitstream -force $out/stream_shell.bit
puts "RESULT: bitstream $out/stream_shell.bit"
