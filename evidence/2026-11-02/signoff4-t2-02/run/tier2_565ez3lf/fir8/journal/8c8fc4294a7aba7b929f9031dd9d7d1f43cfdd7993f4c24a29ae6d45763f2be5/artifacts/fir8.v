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
    integer i;

    wire signed [31:0] total;

    generate
        if ((C0 == 16'sd3)  && (C1 == 16'sd7)  &&
            (C2 == 16'sd12) && (C3 == 16'sd18) &&
            (C4 == 16'sd18) && (C5 == 16'sd12) &&
            (C6 == 16'sd7)  && (C7 == 16'sd3)) begin : default_coefficients
            wire signed [16:0] s0 = {d[0][15], d[0]} + {d[7][15], d[7]};
            wire signed [16:0] s1 = {d[1][15], d[1]} + {d[6][15], d[6]};
            wire signed [16:0] s2 = {d[2][15], d[2]} + {d[5][15], d[5]};
            wire signed [16:0] s3 = {d[3][15], d[3]} + {d[4][15], d[4]};

            wire signed [31:0] e0 = {{15{s0[16]}}, s0};
            wire signed [31:0] e1 = {{15{s1[16]}}, s1};
            wire signed [31:0] e2 = {{15{s2[16]}}, s2};
            wire signed [31:0] e3 = {{15{s3[16]}}, s3};

            wire signed [31:0] p0 = (e0 <<< 1) + e0;
            wire signed [31:0] p1 = (e1 <<< 3) - e1;
            wire signed [31:0] p2 = (e2 <<< 3) + (e2 <<< 2);
            wire signed [31:0] p3 = (e3 <<< 4) + (e3 <<< 1);

            wire [31:0] cs0_sum = p0 ^ p1 ^ p2;
            wire [31:0] cs0_carry = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
            wire [31:0] cs1_sum = cs0_sum ^ cs0_carry ^ p3;
            wire [31:0] cs1_carry =
                ((cs0_sum & cs0_carry) | (cs0_sum & p3) |
                 (cs0_carry & p3)) << 1;

            assign total = cs1_sum + cs1_carry;
        end else if ((C0 == C7) && (C1 == C6) &&
                     (C2 == C5) && (C3 == C4)) begin : symmetric
            wire signed [16:0] s0 = {d[0][15], d[0]} + {d[7][15], d[7]};
            wire signed [16:0] s1 = {d[1][15], d[1]} + {d[6][15], d[6]};
            wire signed [16:0] s2 = {d[2][15], d[2]} + {d[5][15], d[5]};
            wire signed [16:0] s3 = {d[3][15], d[3]} + {d[4][15], d[4]};

            wire signed [31:0] p0 = s0 * C0;
            wire signed [31:0] p1 = s1 * C1;
            wire signed [31:0] p2 = s2 * C2;
            wire signed [31:0] p3 = s3 * C3;

            wire [31:0] cs0_sum = p0 ^ p1 ^ p2;
            wire [31:0] cs0_carry = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
            wire [31:0] cs1_sum = cs0_sum ^ cs0_carry ^ p3;
            wire [31:0] cs1_carry =
                ((cs0_sum & cs0_carry) | (cs0_sum & p3) |
                 (cs0_carry & p3)) << 1;

            assign total = cs1_sum + cs1_carry;
        end else begin : general
            wire signed [31:0] p0 = d[0] * C0;
            wire signed [31:0] p1 = d[1] * C1;
            wire signed [31:0] p2 = d[2] * C2;
            wire signed [31:0] p3 = d[3] * C3;
            wire signed [31:0] p4 = d[4] * C4;
            wire signed [31:0] p5 = d[5] * C5;
            wire signed [31:0] p6 = d[6] * C6;
            wire signed [31:0] p7 = d[7] * C7;

            wire [31:0] cs0_sum = p0 ^ p1 ^ p2;
            wire [31:0] cs0_carry = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
            wire [31:0] cs1_sum = cs0_sum ^ cs0_carry ^ p3;
            wire [31:0] cs1_carry =
                ((cs0_sum & cs0_carry) | (cs0_sum & p3) |
                 (cs0_carry & p3)) << 1;

            wire [31:0] cs2_sum = p4 ^ p5 ^ p6;
            wire [31:0] cs2_carry = ((p4 & p5) | (p4 & p6) | (p5 & p6)) << 1;
            wire [31:0] cs3_sum = cs2_sum ^ cs2_carry ^ p7;
            wire [31:0] cs3_carry =
                ((cs2_sum & cs2_carry) | (cs2_sum & p7) |
                 (cs2_carry & p7)) << 1;

            wire [31:0] group0 = cs1_sum + cs1_carry;
            wire [31:0] group1 = cs3_sum + cs3_carry;
            assign total = group0 + group1;
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];
            y_out <= total;
        end
    end
endmodule