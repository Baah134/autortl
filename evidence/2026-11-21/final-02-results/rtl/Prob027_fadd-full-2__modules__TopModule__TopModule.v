`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire cout,
    output wire sum
);

    (* LUTNM = "full_adder" *)
    assign sum = a ^ b ^ cin;

    (* LUTNM = "full_adder" *)
    assign cout = (a & b) | (a & cin) | (b & cin);

endmodule