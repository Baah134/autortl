`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire       do_sub,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] out,
    output wire       result_is_zero
);
    wire [7:0] b_operand;
    wire [8:0] sum;

    assign b_operand = b ^ {8{do_sub}};
    assign sum = {a, 1'b1} + {b_operand, do_sub};
    assign out = sum[8:1];
    assign result_is_zero = ~|out;
endmodule