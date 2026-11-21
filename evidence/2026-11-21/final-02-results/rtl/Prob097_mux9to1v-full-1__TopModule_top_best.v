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
            wire lower_bank;
            wire upper_bank;
            // Preserve the eight-way mux cone for dedicated mux inference.
            (* keep = "true" *) wire bank_result;

            assign lower_bank = sel[1] ? (sel[0] ? d[bit_index] : c[bit_index])
                                       : (sel[0] ? b[bit_index] : a[bit_index]);
            assign upper_bank = sel[1] ? (sel[0] ? h[bit_index] : g[bit_index])
                                       : (sel[0] ? f[bit_index] : e[bit_index]);
            assign bank_result = sel[2] ? upper_bank : lower_bank;

            assign out[bit_index] = sel[3] ? ((|sel[2:0]) ? 1'b1 : i[bit_index])
                                           : bank_result;
        end
    endgenerate

    // Vivado mapping and simulation-based walking-pattern and mutation checks
    // remain unverified.
endmodule