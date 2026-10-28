# Loads the bitstream into the Basys 3 over USB (volatile; lost on power-off).
# Run with the board plugged in and switched on:
#   vivado -mode batch -source scripts/program.tcl
set root [file normalize [file join [file dirname [info script]] ..]]
set bit  $root/build/basys3_fir4_shell.bit

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
