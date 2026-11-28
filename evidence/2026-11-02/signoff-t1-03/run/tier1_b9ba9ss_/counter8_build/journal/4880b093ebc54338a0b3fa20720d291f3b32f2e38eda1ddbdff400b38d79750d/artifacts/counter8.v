`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module counter8 (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);
    counter8_core u_counter8_core (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count)
    );
endmodule
