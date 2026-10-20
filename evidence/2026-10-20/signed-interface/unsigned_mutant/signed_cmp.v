`timescale 1ns/1ps
module signed_cmp (
    input wire [0:7] a,
    input wire [0:7] b,
    output wire less
);
assign less = a < b;
endmodule
