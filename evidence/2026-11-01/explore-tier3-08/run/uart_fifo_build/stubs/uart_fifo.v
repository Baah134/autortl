`timescale 1ns/1ps
module uart_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire tx
);
    wire [7:0] w_byte_fifo_out_data;
    wire w_byte_fifo_out_valid;
    wire w_uart_tx_tx_ready;
    byte_fifo #( .DEPTH(8) ) u_byte_fifo (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(w_byte_fifo_out_data),
        .out_valid(w_byte_fifo_out_valid),
        .out_ready(w_uart_tx_tx_ready)
    );
    uart_tx #( .CLKS_PER_BIT(16) ) u_uart_tx (
        .clk(clk),
        .rst(rst),
        .tx_data(w_byte_fifo_out_data),
        .tx_valid(w_byte_fifo_out_valid),
        .tx_ready(w_uart_tx_tx_ready),
        .tx(tx)
    );
endmodule
