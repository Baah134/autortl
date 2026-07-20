Build a UART transmitter with an input FIFO, top name `uart_fifo_tx`.
Modules: a synchronous FIFO (depth 16, width 8, valid/ready on both sides)
feeding a UART TX (8N1, baud divisor parameter DIV=868 for 115200 @ 100MHz).
External ports: clk, rst, in_valid/in_ready/in_data[8] (valid_ready), tx (1 bit).
The FIFO uses scoreboard compare mode; the UART TX uses fixed_latency
examples on its shift behavior. Split into exactly two modules plus the
mechanical top.
