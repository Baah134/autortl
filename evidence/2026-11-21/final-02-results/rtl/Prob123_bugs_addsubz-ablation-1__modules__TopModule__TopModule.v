`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire       do_sub,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] out,
    output wire       result_is_zero
);
    wire [7:0] b_adjusted;

    assign b_adjusted = b ^ {8{do_sub}};
    assign out = a + b_adjusted + {7'b0, do_sub};
    assign result_is_zero = ~|out;
endmodule