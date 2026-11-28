`timescale 1ns/1ps
module TopModule_top (
    input wire a,
    input wire b,
    input wire cin,
    output wire cout,
    output wire sum
);
    TopModule u_TopModule (
        .a(a),
        .b(b),
        .cin(cin),
        .cout(cout),
        .sum(sum)
    );
endmodule
