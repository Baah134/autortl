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

    wire [31:0] add_p = s5 ^ c5;
    wire [31:0] add_g = s5 & c5;

    wire [3:0] block_p;
    wire [3:0] block_g;
    wire carry8, carry16, carry24;

    assign block_p[0] = &add_p[7:0];
    assign block_p[1] = &add_p[15:8];
    assign block_p[2] = &add_p[23:16];
    assign block_p[3] = &add_p[31:24];

    assign block_g[0] = add_g[7] | (add_p[7] & add_g[6]) |
                        (add_p[7] & add_p[6] & add_g[5]) |
                        (add_p[7] & add_p[6] & add_p[5] & add_g[4]) |
                        (add_p[7] & add_p[6] & add_p[5] & add_p[4] & add_g[3]) |
                        (add_p[7] & add_p[6] & add_p[5] & add_p[4] & add_p[3] & add_g[2]) |
                        (add_p[7] & add_p[6] & add_p[5] & add_p[4] & add_p[3] & add_p[2] & add_g[1]) |
                        (add_p[7] & add_p[6] & add_p[5] & add_p[4] & add_p[3] & add_p[2] & add_p[1] & add_g[0]);
    assign block_g[1] = add_g[15] | (add_p[15] & add_g[14]) |
                        (add_p[15] & add_p[14] & add_g[13]) |
                        (add_p[15] & add_p[14] & add_p[13] & add_g[12]) |
                        (add_p[15] & add_p[14] & add_p[13] & add_p[12] & add_g[11]) |
                        (add_p[15] & add_p[14] & add_p[13] & add_p[12] & add_p[11] & add_g[10]) |
                        (add_p[15] & add_p[14] & add_p[13] & add_p[12] & add_p[11] & add_p[10] & add_g[9]) |
                        (add_p[15] & add_p[14] & add_p[13] & add_p[12] & add_p[11] & add_p[10] & add_p[9] & add_g[8]);
    assign block_g[2] = add_g[23] | (add_p[23] & add_g[22]) |
                        (add_p[23] & add_p[22] & add_g[21]) |
                        (add_p[23] & add_p[22] & add_p[21] & add_g[20]) |
                        (add_p[23] & add_p[22] & add_p[21] & add_p[20] & add_g[19]) |
                        (add_p[23] & add_p[22] & add_p[21] & add_p[20] & add_p[19] & add_g[18]) |
                        (add_p[23] & add_p[22] & add_p[21] & add_p[20] & add_p[19] & add_p[18] & add_g[17]) |
                        (add_p[23] & add_p[22] & add_p[21] & add_p[20] & add_p[19] & add_p[18] & add_p[17] & add_g[16]);
    assign block_g[3] = add_g[31] | (add_p[31] & add_g[30]) |
                        (add_p[31] & add_p[30] & add_g[29]) |
                        (add_p[31] & add_p[30] & add_p[29] & add_g[28]) |
                        (add_p[31] & add_p[30] & add_p[29] & add_p[28] & add_g[27]) |
                        (add_p[31] & add_p[30] & add_p[29] & add_p[28] & add_p[27] & add_g[26]) |
                        (add_p[31] & add_p[30] & add_p[29] & add_p[28] & add_p[27] & add_p[26] & add_g[25]) |
                        (add_p[31] & add_p[30] & add_p[29] & add_p[28] & add_p[27] & add_p[26] & add_p[25] & add_g[24]);

    assign carry8  = block_g[0];
    assign carry16 = block_g[1] | (block_p[1] & block_g[0]);
    assign carry24 = block_g[2] | (block_p[2] & block_g[1]) |
                     (block_p[2] & block_p[1] & block_g[0]);

    wire [7:0] sum0 = s5[7:0]   + c5[7:0];
    wire [7:0] sum1 = s5[15:8]  + c5[15:8]  + carry8;
    wire [7:0] sum2 = s5[23:16] + c5[23:16] + carry16;
    wire [7:0] sum3 = s5[31:24] + c5[31:24] + carry24;
    wire signed [31:0] total = {sum3, sum2, sum1, sum0};

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