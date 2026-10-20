`timescale 1ns/1ps
module signed_top (
    input wire signed [0:7] a,
    input wire signed [0:7] b,
    output wire less
);
    signed_cmp u_signed_cmp (
        .a(a),
        .b(b),
        .less(less)
    );
endmodule
