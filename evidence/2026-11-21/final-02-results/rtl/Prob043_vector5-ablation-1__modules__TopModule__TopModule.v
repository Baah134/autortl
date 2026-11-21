`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire        a,
    input  wire        b,
    input  wire        c,
    input  wire        d,
    input  wire        e,
    output wire [24:0] out
);

    wire ab, ac, ad, ae;
    wire bc, bd, be;
    wire cd, ce;
    wire de;

    assign ab = a ~^ b;
    assign ac = a ~^ c;
    assign ad = a ~^ d;
    assign ae = a ~^ e;
    assign bc = b ~^ c;
    assign bd = b ~^ d;
    assign be = b ~^ e;
    assign cd = c ~^ d;
    assign ce = c ~^ e;
    assign de = d ~^ e;

    assign out = {
        1'b1, ab,   ac,   ad,   ae,
        ab,   1'b1, bc,   bd,   be,
        ac,   bc,   1'b1, cd,   ce,
        ad,   bd,   cd,   1'b1, de,
        ae,   be,   ce,   de,   1'b1
    };

endmodule