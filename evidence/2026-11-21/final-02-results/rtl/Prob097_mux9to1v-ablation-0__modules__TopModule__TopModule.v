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

    wire [15:0] mux_ab = sel[0] ? b : a;
    wire [15:0] mux_cd = sel[0] ? d : c;
    wire [15:0] mux_ef = sel[0] ? f : e;
    wire [15:0] mux_gh = sel[0] ? h : g;

    wire [15:0] mux_ad = sel[1] ? mux_cd : mux_ab;
    wire [15:0] mux_eh = sel[1] ? mux_gh : mux_ef;
    wire [15:0] mux_ah = sel[2] ? mux_eh : mux_ad;

    wire invalid_high = |sel[2:0];
    wire [15:0] mux_high = invalid_high ? 16'hFFFF : i;

    assign out = sel[3] ? mux_high : mux_ah;

endmodule