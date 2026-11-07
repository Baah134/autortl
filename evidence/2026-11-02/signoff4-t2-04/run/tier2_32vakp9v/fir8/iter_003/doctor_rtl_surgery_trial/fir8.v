`timescale 1ns/1ps
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    output reg  signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;

    (* keep = "true" *) reg signed [15:0] d_low  [0:7];
    (* keep = "true" *) reg signed [15:0] d_high [0:7];
    integer i;

    wire signed [31:0] sum_all;

    generate
        if ((C0 == C7) && (C1 == C6) && (C2 == C5) && (C3 == C4)) begin : symmetric_coefficients
            wire signed [16:0] x0_ext = {d_low[0][15], d_low[0]};
            wire signed [16:0] x1_ext = {d_low[1][15], d_low[1]};
            wire signed [16:0] x2_ext = {d_low[2][15], d_low[2]};
            wire signed [16:0] x3_ext = {d_low[3][15], d_low[3]};
            wire signed [16:0] x4_ext = {d_high[4][15], d_high[4]};
            wire signed [16:0] x5_ext = {d_high[5][15], d_high[5]};
            wire signed [16:0] x6_ext = {d_high[6][15], d_high[6]};
            wire signed [16:0] x7_ext = {d_high[7][15], d_high[7]};

            wire signed [16:0] pair0 = x0_ext + x7_ext;
            wire signed [16:0] pair1 = x1_ext + x6_ext;
            wire signed [16:0] pair2 = x2_ext + x5_ext;
            wire signed [16:0] pair3 = x3_ext + x4_ext;

            wire signed [32:0] product0 = pair0 * C0;
            wire signed [32:0] product1 = pair1 * C1;
            wire signed [32:0] product2 = pair2 * C2;
            wire signed [32:0] product3 = pair3 * C3;

            wire signed [31:0] p0 = product0[31:0];
            wire signed [31:0] p1 = product1[31:0];
            wire signed [31:0] p2 = product2[31:0];
            wire signed [31:0] p3 = product3[31:0];

            (* use_dsp = "no" *) wire signed [31:0] s01 = p0 + p1;
            (* use_dsp = "no" *) wire signed [31:0] s23 = p2 + p3;
            (* use_dsp = "no" *) assign sum_all = s01 + s23;
        end else begin : generic_coefficients
            wire signed [31:0] x0_ext = {{16{d_low[0][15]}}, d_low[0]};
            wire signed [31:0] x1_ext = {{16{d_low[1][15]}}, d_low[1]};
            wire signed [31:0] x2_ext = {{16{d_low[2][15]}}, d_low[2]};
            wire signed [31:0] x3_ext = {{16{d_low[3][15]}}, d_low[3]};
            wire signed [31:0] x4_ext = {{16{d_high[4][15]}}, d_high[4]};
            wire signed [31:0] x5_ext = {{16{d_high[5][15]}}, d_high[5]};
            wire signed [31:0] x6_ext = {{16{d_high[6][15]}}, d_high[6]};
            wire signed [31:0] x7_ext = {{16{d_high[7][15]}}, d_high[7]};

            wire signed [31:0] c0_ext = {{16{C0[15]}}, C0};
            wire signed [31:0] c1_ext = {{16{C1[15]}}, C1};
            wire signed [31:0] c2_ext = {{16{C2[15]}}, C2};
            wire signed [31:0] c3_ext = {{16{C3[15]}}, C3};
            wire signed [31:0] c4_ext = {{16{C4[15]}}, C4};
            wire signed [31:0] c5_ext = {{16{C5[15]}}, C5};
            wire signed [31:0] c6_ext = {{16{C6[15]}}, C6};
            wire signed [31:0] c7_ext = {{16{C7[15]}}, C7};

            wire signed [31:0] p0 = x0_ext * c0_ext;
            wire signed [31:0] p1 = x1_ext * c1_ext;
            wire signed [31:0] p2 = x2_ext * c2_ext;
            wire signed [31:0] p3 = x3_ext * c3_ext;
            wire signed [31:0] p4 = x4_ext * c4_ext;
            wire signed [31:0] p5 = x5_ext * c5_ext;
            wire signed [31:0] p6 = x6_ext * c6_ext;
            wire signed [31:0] p7 = x7_ext * c7_ext;

            (* use_dsp = "no" *) wire signed [31:0] s01 = p0 + p1;
            (* use_dsp = "no" *) wire signed [31:0] s23 = p2 + p3;
            (* use_dsp = "no" *) wire signed [31:0] s45 = p4 + p5;
            (* use_dsp = "no" *) wire signed [31:0] s67 = p6 + p7;

            (* use_dsp = "no" *) wire signed [31:0] s0123 = s01 + s23;
            (* use_dsp = "no" *) wire signed [31:0] s4567 = s45 + s67;
            (* use_dsp = "no" *) assign sum_all = s0123 + s4567;
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) begin
                d_low[i]  <= 16'sd0;
                d_high[i] <= 16'sd0;
            end
            y_out <= 32'sd0;
        end else begin
            d_low[0]  <= x_in;
            d_high[0] <= x_in;
            for (i = 1; i < 8; i = i + 1) begin
                d_low[i]  <= d_low[i-1];
                d_high[i] <= d_high[i-1];
            end
            y_out <= sum_all;
        end
    end
endmodule