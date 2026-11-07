`timescale 1ns/1ps
// @latency 2
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module elastic_dot4 (
    input wire clk,
    input wire rst,
    input wire [7:0] a0,
    input wire [7:0] b0,
    input wire [7:0] a1,
    input wire [7:0] b1,
    input wire [7:0] a2,
    input wire [7:0] b2,
    input wire [7:0] a3,
    input wire [7:0] b3,
    input wire in_valid,
    output wire in_ready,
    output wire [17:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    elastic_dot4_core u_elastic_dot4_core (
        .clk(clk),
        .rst(rst),
        .a0(a0),
        .b0(b0),
        .a1(a1),
        .b1(b1),
        .a2(a2),
        .b2(b2),
        .a3(a3),
        .b3(b3),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule
