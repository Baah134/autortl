# Loads a bitstream into the Basys 3 over USB (volatile; lost on power-off).
#   vivado -mode batch -source program.tcl -tclargs <bitstream.bit>
if {[llength $argv] != 1} {
    error "usage: program.tcl <bitstream.bit>"
}
set bit [file normalize [lindex $argv 0]]
if {![file isfile $bit]} {
    error "bitstream not found: $bit"
}

open_hw_manager
connect_hw_server
open_hw_target

set dev [lindex [get_hw_devices xc7a35t*] 0]
if {$dev eq ""} {
    error "No xc7a35t device found. Is the board connected and powered on?"
}
current_hw_device $dev
set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev
puts "RESULT: programmed $dev with $bit"

close_hw_target
disconnect_hw_server
close_hw_manager
