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

    reg signed [15:0] d [0:7];
    reg signed [31:0] p0, p1, p2, p3, p4, p5, p6, p7;
    integer i;

    wire signed [31:0] x_in_ext = {{16{x_in[15]}}, x_in};
    wire signed [31:0] d0_ext = {{16{d[0][15]}}, d[0]};
    wire signed [31:0] d1_ext = {{16{d[1][15]}}, d[1]};
    wire signed [31:0] d2_ext = {{16{d[2][15]}}, d[2]};
    wire signed [31:0] d3_ext = {{16{d[3][15]}}, d[3]};
    wire signed [31:0] d4_ext = {{16{d[4][15]}}, d[4]};
    wire signed [31:0] d5_ext = {{16{d[5][15]}}, d[5]};
    wire signed [31:0] d6_ext = {{16{d[6][15]}}, d[6]};

    wire signed [31:0] c0_ext = {{16{C0[15]}}, C0};
    wire signed [31:0] c1_ext = {{16{C1[15]}}, C1};
    wire signed [31:0] c2_ext = {{16{C2[15]}}, C2};
    wire signed [31:0] c3_ext = {{16{C3[15]}}, C3};
    wire signed [31:0] c4_ext = {{16{C4[15]}}, C4};
    wire signed [31:0] c5_ext = {{16{C5[15]}}, C5};
    wire signed [31:0] c6_ext = {{16{C6[15]}}, C6};
    wire signed [31:0] c7_ext = {{16{C7[15]}}, C7};

    wire signed [31:0] m0 = x_in_ext * c0_ext;
    wire signed [31:0] m1 = d0_ext   * c1_ext;
    wire signed [31:0] m2 = d1_ext   * c2_ext;
    wire signed [31:0] m3 = d2_ext   * c3_ext;
    wire signed [31:0] m4 = d3_ext   * c4_ext;
    wire signed [31:0] m5 = d4_ext   * c5_ext;
    wire signed [31:0] m6 = d5_ext   * c6_ext;
    wire signed [31:0] m7 = d6_ext   * c7_ext;

    wire [31:0] s1 = p0 ^ p1 ^ p2;
    wire [31:0] c1 = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
    wire [31:0] s2 = p3 ^ p4 ^ p5;
    wire [31:0] c2 = ((p3 & p4) | (p3 & p5) | (p4 & p5)) << 1;

    wire [31:0] s3 = s1 ^ c1 ^ s2;
    wire [31:0] c3 = ((s1 & c1) | (s1 & s2) | (c1 & s2)) << 1;
    wire [31:0] s4 = c2 ^ p6 ^ p7;
    wire [31:0] c4 = ((c2 & p6) | (c2 & p7) | (p6 & p7)) << 1;

    wire [31:0] s5 = s3 ^ c3 ^ s4;
    wire [31:0] c5 = ((s3 & c3) | (s3 & s4) | (c3 & s4)) << 1;

    wire [31:0] s6 = s5 ^ c5 ^ c4;
    wire [31:0] c6 = ((s5 & c5) | (s5 & c4) | (c5 & c4)) << 1;

    wire [8:0] cs_low = {1'b0, s6[7:0]} + {1'b0, c6[7:0]};

    wire [8:0] cs1_cin0 = {1'b0, s6[15:8]} + {1'b0, c6[15:8]};
    wire [8:0] cs1_cin1 = cs1_cin0 + 9'd1;
    wire       cs1_carry = cs_low[8] ? cs1_cin1[8] : cs1_cin0[8];
    wire [7:0] cs1_sum   = cs_low[8] ? cs1_cin1[7:0] : cs1_cin0[7:0];

    wire [8:0] cs2_cin0 = {1'b0, s6[23:16]} + {1'b0, c6[23:16]};
    wire [8:0] cs2_cin1 = cs2_cin0 + 9'd1;
    wire       cs2_carry = cs1_carry ? cs2_cin1[8] : cs2_cin0[8];
    wire [7:0] cs2_sum   = cs1_carry ? cs2_cin1[7:0] : cs2_cin0[7:0];

    wire [8:0] cs3_cin0 = {1'b0, s6[31:24]} + {1'b0, c6[31:24]};
    wire [8:0] cs3_cin1 = cs3_cin0 + 9'd1;
    wire [7:0] cs3_sum  = cs2_carry ? cs3_cin1[7:0] : cs3_cin0[7:0];

    wire signed [31:0] sum_all = {cs3_sum, cs2_sum, cs1_sum, cs_low[7:0]};

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            p0 <= 32'sd0;
            p1 <= 32'sd0;
            p2 <= 32'sd0;
            p3 <= 32'sd0;
            p4 <= 32'sd0;
            p5 <= 32'sd0;
            p6 <= 32'sd0;
            p7 <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];

            p0 <= m0;
            p1 <= m1;
            p2 <= m2;
            p3 <= m3;
            p4 <= m4;
            p5 <= m5;
            p6 <= m6;
            p7 <= m7;

            y_out <= sum_all;
        end
    end
endmodule