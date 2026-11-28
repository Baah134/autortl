`timescale 1ns/1ps
module uart_fifo_tx (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire tx
);
    wire w_sync_fifo16_out_valid;
    wire w_uart_tx_tx_ready;
    wire [7:0] w_sync_fifo16_out_data;
    sync_fifo16 u_sync_fifo16 (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_data(in_data),
        .out_valid(w_sync_fifo16_out_valid),
        .out_ready(w_uart_tx_tx_ready),
        .out_data(w_sync_fifo16_out_data)
    );
    uart_tx #( .DIV(868) ) u_uart_tx (
        .clk(clk),
        .rst(rst),
        .in_valid(w_sync_fifo16_out_valid),
        .tx_ready(w_uart_tx_tx_ready),
        .in_data(w_sync_fifo16_out_data),
        .tx(tx)
    );
endmodule
