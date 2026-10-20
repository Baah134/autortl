`timescale 1ns/1ps
module signed_cmp (
    input wire signed [0:7] a,
    input wire signed [0:7] b,
    output wire less
);
assign less = a < b;
endmodule
