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

    reg signed [31:0] prod [0:63];
    integer i;
    integer j;

    wire signed [31:0] in_product0 = x_in * C0;
    wire signed [31:0] in_product1 = x_in * C1;
    wire signed [31:0] in_product2 = x_in * C2;
    wire signed [31:0] in_product3 = x_in * C3;
    wire signed [31:0] in_product4 = x_in * C4;
    wire signed [31:0] in_product5 = x_in * C5;
    wire signed [31:0] in_product6 = x_in * C6;
    wire signed [31:0] in_product7 = x_in * C7;

    wire [31:0] a0 = prod[0];
    wire [31:0] a1 = prod[63];
    wire [31:0] a2 = prod[9];
    wire [31:0] a3 = prod[54];
    wire [31:0] a4 = prod[18];
    wire [31:0] a5 = prod[45];
    wire [31:0] a6 = prod[27];
    wire [31:0] a7 = prod[36];

    wire [31:0] s0 = a0 ^ a1 ^ a2;
    wire [31:0] c0 = ((a0 & a1) | (a0 & a2) | (a1 & a2)) << 1;
    wire [31:0] s1 = a3 ^ a4 ^ a5;
    wire [31:0] c1 = ((a3 & a4) | (a3 & a5) | (a4 & a5)) << 1;

    wire [31:0] s2 = s0 ^ c0 ^ s1;
    wire [31:0] c2 = ((s0 & c0) | (s0 & s1) | (c0 & s1)) << 1;
    wire [31:0] s3 = c1 ^ a6 ^ a7;
    wire [31:0] c3 = ((c1 & a6) | (c1 & a7) | (a6 & a7)) << 1;

    wire [31:0] s4 = s2 ^ c2 ^ s3;
    wire [31:0] c4 = ((s2 & c2) | (s2 & s3) | (c2 & s3)) << 1;
    wire [31:0] s5 = s4 ^ c4 ^ c3;
    wire [31:0] c5 = ((s4 & c4) | (s4 & c3) | (c4 & c3)) << 1;

    wire [8:0] sum0_cin0 = {1'b0, s5[7:0]} + {1'b0, c5[7:0]};
    wire [8:0] sum1_cin0 = {1'b0, s5[15:8]} + {1'b0, c5[15:8]};
    wire [8:0] sum1_cin1 = {1'b0, s5[15:8]} + {1'b0, c5[15:8]} + 9'd1;
    wire [8:0] sum2_cin0 = {1'b0, s5[23:16]} + {1'b0, c5[23:16]};
    wire [8:0] sum2_cin1 = {1'b0, s5[23:16]} + {1'b0, c5[23:16]} + 9'd1;
    wire [8:0] sum3_cin0 = {1'b0, s5[31:24]} + {1'b0, c5[31:24]};
    wire [8:0] sum3_cin1 = {1'b0, s5[31:24]} + {1'b0, c5[31:24]} + 9'd1;

    wire carry1 = sum0_cin0[8];
    wire [8:0] selected1 = carry1 ? sum1_cin1 : sum1_cin0;
    wire carry2 = selected1[8];
    wire [8:0] selected2 = carry2 ? sum2_cin1 : sum2_cin0;
    wire carry3 = selected2[8];
    wire [8:0] selected3 = carry3 ? sum3_cin1 : sum3_cin0;

    wire signed [31:0] total = {
        selected3[7:0],
        selected2[7:0],
        selected1[7:0],
        sum0_cin0[7:0]
    };

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 64; i = i + 1)
                prod[i] <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            for (i = 0; i < 8; i = i + 1) begin
                case (i)
                    0: prod[0]  <= in_product0;
                    1: prod[8]  <= in_product1;
                    2: prod[16] <= in_product2;
                    3: prod[24] <= in_product3;
                    4: prod[32] <= in_product4;
                    5: prod[40] <= in_product5;
                    6: prod[48] <= in_product6;
                    7: prod[56] <= in_product7;
                endcase
                for (j = 1; j <= i; j = j + 1)
                    prod[i*8+j] <= prod[i*8+j-1];
            end
            y_out <= total;
        end
    end
endmodule