## Basys 3 pins, taken from Digilent's Basys-3-Master.xdc.

## 100 MHz clock
set_property -dict { PACKAGE_PIN W5   IOSTANDARD LVCMOS33 } [get_ports clk]
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports clk]

## Center button (reset)
set_property -dict { PACKAGE_PIN U18  IOSTANDARD LVCMOS33 } [get_ports btnC]

## USB-UART bridge
set_property -dict { PACKAGE_PIN B18  IOSTANDARD LVCMOS33 } [get_ports RsRx]
set_property -dict { PACKAGE_PIN A18  IOSTANDARD LVCMOS33 } [get_ports RsTx]

## LD0-LD7: completed result count (low byte)
set_property -dict { PACKAGE_PIN U16  IOSTANDARD LVCMOS33 } [get_ports {led[0]}]
set_property -dict { PACKAGE_PIN E19  IOSTANDARD LVCMOS33 } [get_ports {led[1]}]
set_property -dict { PACKAGE_PIN U19  IOSTANDARD LVCMOS33 } [get_ports {led[2]}]
set_property -dict { PACKAGE_PIN V19  IOSTANDARD LVCMOS33 } [get_ports {led[3]}]
set_property -dict { PACKAGE_PIN W18  IOSTANDARD LVCMOS33 } [get_ports {led[4]}]
set_property -dict { PACKAGE_PIN U15  IOSTANDARD LVCMOS33 } [get_ports {led[5]}]
set_property -dict { PACKAGE_PIN U14  IOSTANDARD LVCMOS33 } [get_ports {led[6]}]
set_property -dict { PACKAGE_PIN V14  IOSTANDARD LVCMOS33 } [get_ports {led[7]}]

## LD14: break (restart) received; LD15: input FIFO overflow. Both latch until btnC.
set_property -dict { PACKAGE_PIN P1   IOSTANDARD LVCMOS33 } [get_ports led_break]
set_property -dict { PACKAGE_PIN L1   IOSTANDARD LVCMOS33 } [get_ports led_overflow]

## The button and UART RX are asynchronous and pass through two-flop
## synchronizers; UART TX and the LEDs are slow outputs. None of these
## have a timing relationship to clk worth constraining.
set_false_path -from [get_ports {btnC RsRx}]
set_false_path -to   [get_ports {RsTx led[*] led_break led_overflow}]

## Configuration
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
