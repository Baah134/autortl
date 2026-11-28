`timescale 1ns/1ps
// @latency 0
module TopModule_top (
    input wire [15:0] a,
    input wire [15:0] b,
    input wire [15:0] c,
    input wire [15:0] d,
    input wire [15:0] e,
    input wire [15:0] f,
    input wire [15:0] g,
    input wire [15:0] h,
    input wire [15:0] i,
    input wire [3:0] sel,
    output wire [15:0] out
);
    genvar bit_index;
    generate
        for (bit_index = 0; bit_index < 16; bit_index = bit_index + 1) begin : bit_slice
            wire mux_ad;
            wire mux_eh;
            (* keep = "true", muxf_mapping = "yes" *) wire mux_ah;

            assign mux_ad = sel[1] ? (sel[0] ? d[bit_index] : c[bit_index])
                                   : (sel[0] ? b[bit_index] : a[bit_index]);
            assign mux_eh = sel[1] ? (sel[0] ? h[bit_index] : g[bit_index])
                                   : (sel[0] ? f[bit_index] : e[bit_index]);
            assign mux_ah = sel[2] ? mux_eh : mux_ad;

            assign out[bit_index] = sel[3]
                                  ? ((|sel[2:0]) ? 1'b1 : i[bit_index])
                                  : mux_ah;
        end
    endgenerate

    // By inspection, codes 0 through 8 pass the selected word bit for bit,
    // including every walking-one and walking-zero pattern. Codes 9 through
    // 15 drive every bit high. Simulation and routed resource counts are unverified.
endmodule