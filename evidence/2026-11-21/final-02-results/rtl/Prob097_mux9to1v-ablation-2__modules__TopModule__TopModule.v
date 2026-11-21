`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [15:0] a,
    input  wire [15:0] b,
    input  wire [15:0] c,
    input  wire [15:0] d,
    input  wire [15:0] e,
    input  wire [15:0] f,
    input  wire [15:0] g,
    input  wire [15:0] h,
    input  wire [15:0] i,
    input  wire [3:0]  sel,
    output wire [15:0] out
);

    (* keep = "true" *) wire [15:0] group_abcd;
    (* keep = "true" *) wire [15:0] group_efgh;
    (* keep = "true" *) wire select_i;

    assign group_abcd = sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
    assign group_efgh = sel[1] ? (sel[0] ? h : g) : (sel[0] ? f : e);
    assign select_i = (sel == 4'd8);

    assign out = sel[3] ? (select_i ? i : 16'hFFFF)
                        : (sel[2] ? group_efgh : group_abcd);

endmodule