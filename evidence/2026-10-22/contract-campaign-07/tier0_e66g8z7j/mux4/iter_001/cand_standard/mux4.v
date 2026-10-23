`timescale 1ns/1ps
module mux4 (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    input  wire [1:0] sel,
    output wire [7:0] y
);
    wire [7:0] muxf7_lo;
    wire [7:0] muxf7_hi;
    wire [7:0] muxf8_out;
    reg  [7:0] y_reg;

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_mux
            MUXF7 muxf7_0 (
                .O  (muxf7_lo[i]),
                .I0 (a[i]),
                .I1 (b[i]),
                .S  (sel[0])
            );

            MUXF7 muxf7_1 (
                .O  (muxf7_hi[i]),
                .I0 (c[i]),
                .I1 (d[i]),
                .S  (sel[0])
            );

            MUXF8 muxf8_0 (
                .O  (muxf8_out[i]),
                .I0 (muxf7_lo[i]),
                .I1 (muxf7_hi[i]),
                .S  (sel[1])
            );
        end
    endgenerate

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= muxf8_out;
    end

    assign y = y_reg;
endmodule