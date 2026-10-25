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
    wire [7:0] ab;
    wire [7:0] cd;
    wire [7:0] mux_out;
    reg  [7:0] y_reg;

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : mux_bit
            MUXF7 mux_ab (
                .I0(a[i]),
                .I1(b[i]),
                .S(sel[0]),
                .O(ab[i])
            );

            MUXF7 mux_cd (
                .I0(c[i]),
                .I1(d[i]),
                .S(sel[0]),
                .O(cd[i])
            );

            MUXF8 mux_final (
                .I0(ab[i]),
                .I1(cd[i]),
                .S(sel[1]),
                .O(mux_out[i])
            );
        end
    endgenerate

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= mux_out;
    end

    assign y = y_reg;
endmodule