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
    (* keep = "true" *) wire [15:0] mux_abcd;
    (* keep = "true" *) wire [15:0] mux_efgh;
    (* keep = "true" *) wire sel_low_zero;

    assign sel_low_zero = ~|sel[2:0];

    assign mux_abcd = sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
    assign mux_efgh = sel[1] ? (sel[0] ? h : g) : (sel[0] ? f : e);

    assign out = sel[3] ? (sel_low_zero ? i : 16'hFFFF)
                        : (sel[2] ? mux_efgh : mux_abcd);
endmodule