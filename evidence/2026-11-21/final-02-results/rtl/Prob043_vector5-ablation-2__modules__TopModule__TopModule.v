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

    wire eq_ab, eq_ac, eq_ad, eq_ae;
    wire eq_bc, eq_bd, eq_be;
    wire eq_cd, eq_ce;
    wire eq_de;

    assign eq_ab = a ~^ b;
    assign eq_ac = a ~^ c;
    assign eq_ad = a ~^ d;
    assign eq_ae = a ~^ e;
    assign eq_bc = b ~^ c;
    assign eq_bd = b ~^ d;
    assign eq_be = b ~^ e;
    assign eq_cd = c ~^ d;
    assign eq_ce = c ~^ e;
    assign eq_de = d ~^ e;

    assign out = {
        1'b1,  eq_ab, eq_ac, eq_ad, eq_ae,
        eq_ab, 1'b1,  eq_bc, eq_bd, eq_be,
        eq_ac, eq_bc, 1'b1,  eq_cd, eq_ce,
        eq_ad, eq_bd, eq_cd, 1'b1,  eq_de,
        eq_ae, eq_be, eq_ce, eq_de, 1'b1
    };

endmodule