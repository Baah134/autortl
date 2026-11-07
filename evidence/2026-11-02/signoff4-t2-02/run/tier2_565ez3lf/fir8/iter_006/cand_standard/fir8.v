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

    wire signed [16:0] pair0 = {d[0][15], d[0]} + {d[7][15], d[7]};
    wire signed [16:0] pair1 = {d[1][15], d[1]} + {d[6][15], d[6]};
    wire signed [16:0] pair2 = {d[2][15], d[2]} + {d[5][15], d[5]};
    wire signed [16:0] pair3 = {d[3][15], d[3]} + {d[4][15], d[4]};

    wire signed [31:0] pair0_32 = {{15{pair0[16]}}, pair0};
    wire signed [31:0] pair1_32 = {{15{pair1[16]}}, pair1};
    wire signed [31:0] pair2_32 = {{15{pair2[16]}}, pair2};
    wire signed [31:0] pair3_32 = {{15{pair3[16]}}, pair3};

    wire signed [31:0] term0 = (pair0_32 <<< 1) + pair0_32;
    wire signed [31:0] term1 = (pair1_32 <<< 3) - pair1_32;
    wire signed [31:0] term2 = (pair2_32 <<< 3) + (pair2_32 <<< 2);
    wire signed [31:0] term3 = (pair3_32 <<< 4) + (pair3_32 <<< 1);

    wire [31:0] csa1_sum = term0 ^ term1 ^ term2;
    wire [31:0] csa1_carry =
        ((term0 & term1) | (term0 & term2) | (term1 & term2)) << 1;
    wire [31:0] csa2_sum = csa1_sum ^ csa1_carry ^ term3;
    wire [31:0] csa2_carry =
        ((csa1_sum & csa1_carry) |
         (csa1_sum & term3) |
         (csa1_carry & term3)) << 1;
    wire signed [31:0] default_sum = csa2_sum + csa2_carry;

    wire signed [31:0] generic_sum =
        d[0] * C0 + d[1] * C1 + d[2] * C2 + d[3] * C3 +
        d[4] * C4 + d[5] * C5 + d[6] * C6 + d[7] * C7;

    wire signed [31:0] sample_sum;

    generate
        if ((C0 == 16'sd3)  && (C1 == 16'sd7)  &&
            (C2 == 16'sd12) && (C3 == 16'sd18) &&
            (C4 == 16'sd18) && (C5 == 16'sd12) &&
            (C6 == 16'sd7)  && (C7 == 16'sd3)) begin : default_coefficients
            assign sample_sum = default_sum;
        end else begin : other_coefficients
            assign sample_sum = generic_sum;
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
            y_out <= sample_sum;
        end
    end
endmodule