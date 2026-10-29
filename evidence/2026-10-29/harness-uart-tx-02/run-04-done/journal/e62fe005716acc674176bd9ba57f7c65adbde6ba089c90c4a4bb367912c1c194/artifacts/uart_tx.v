`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module uart_tx (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire tx
);
    wire [1:0] uart_outputs;

    uart_tx_core #( .DIV(868) ) u_uart_tx_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(uart_outputs[1]),
        .tx(uart_outputs[0])
    );

    assign in_ready = uart_outputs[1];
    assign tx = uart_outputs[0];
endmodule