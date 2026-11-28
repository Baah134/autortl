`timescale 1ns/1ps
// @latency 0
module TopModule_top (
    input wire do_sub,
    input wire [7:0] a,
    input wire [7:0] b,
    output wire [7:0] out,
    output wire result_is_zero
);
    wire [7:0] b_effective;
    wire [8:0] sum_with_carry_in;

    assign b_effective = b ^ {8{do_sub}};

    // The low bit injects do_sub as the carry-in to a single inferred adder.
    assign sum_with_carry_in = {a, 1'b1} + {b_effective, do_sub};
    assign out = sum_with_carry_in[8:1];
    assign result_is_zero = ~|out;
endmodule