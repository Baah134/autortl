`timescale 1ns/1ps
// @latency 3
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module signed_fir4 (
    input wire clk,
    input wire rst,
    input wire signed [7:0] x,
    input wire in_valid,
    output wire in_ready,
    output wire signed [12:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    signed_fir4_core u_signed_fir4_core (
        .clk(clk),
        .rst(rst),
        .x(x),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule
