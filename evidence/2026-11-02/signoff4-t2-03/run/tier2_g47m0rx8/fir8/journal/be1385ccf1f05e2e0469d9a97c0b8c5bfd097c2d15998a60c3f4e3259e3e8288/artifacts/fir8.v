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

    function signed [31:0] mul_shift_add;
        input signed [15:0] a;
        input signed [15:0] b;
        reg signed [31:0] ax;
        reg signed [31:0] accum;
        integer j;
        begin
            ax = {{16{a[15]}}, a};
            accum = 32'sd0;
            for (j = 0; j < 15; j = j + 1)
                if (b[j])
                    accum = accum + (ax << j);
            if (b[15])
                accum = accum - (ax << 15);
            mul_shift_add = accum;
        end
    endfunction

    wire signed [31:0] p0 = mul_shift_add(d[0], C0);
    wire signed [31:0] p1 = mul_shift_add(d[1], C1);
    wire signed [31:0] p2 = mul_shift_add(d[2], C2);
    wire signed [31:0] p3 = mul_shift_add(d[3], C3);
    wire signed [31:0] p4 = mul_shift_add(d[4], C4);
    wire signed [31:0] p5 = mul_shift_add(d[5], C5);
    wire signed [31:0] p6 = mul_shift_add(d[6], C6);
    wire signed [31:0] p7 = mul_shift_add(d[7], C7);

    wire [31:0] s0 = p0 ^ p1 ^ p2;
    wire [31:0] c0 = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
    wire [31:0] s1 = p3 ^ p4 ^ p5;
    wire [31:0] c1 = ((p3 & p4) | (p3 & p5) | (p4 & p5)) << 1;

    wire [31:0] s2 = s0 ^ c0 ^ s1;
    wire [31:0] c2 = ((s0 & c0) | (s0 & s1) | (c0 & s1)) << 1;
    wire [31:0] s3 = c1 ^ p6 ^ p7;
    wire [31:0] c3 = ((c1 & p6) | (c1 & p7) | (p6 & p7)) << 1;

    wire [31:0] s4 = s2 ^ c2 ^ s3;
    wire [31:0] c4 = ((s2 & c2) | (s2 & s3) | (c2 & s3)) << 1;

    wire [31:0] s5 = s4 ^ c4 ^ c3;
    wire [31:0] c5 = ((s4 & c4) | (s4 & c3) | (c4 & c3)) << 1;

    wire [31:0] bit_p = s5 ^ c5;
    wire [31:0] bit_g = s5 & c5;

    wire block_p0 = &bit_p[7:0];
    wire block_p1 = &bit_p[15:8];
    wire block_p2 = &bit_p[23:16];
    wire block_p3 = &bit_p[31:24];

    wire [8:0] block_g0_ext = {1'b0, s5[7:0]} + {1'b0, c5[7:0]};
    wire [8:0] block_g1_ext = {1'b0, s5[15:8]} + {1'b0, c5[15:8]};
    wire [8:0] block_g2_ext = {1'b0, s5[23:16]} + {1'b0, c5[23:16]};
    wire [8:0] block_g3_ext = {1'b0, s5[31:24]} + {1'b0, c5[31:24]};

    wire block_g0 = block_g0_ext[8];
    wire block_g1 = block_g1_ext[8];
    wire block_g2 = block_g2_ext[8];
    wire block_g3 = block_g3_ext[8];

    wire carry8  = block_g0;
    wire carry16 = block_g1 | (block_p1 & block_g0);
    wire carry24 = block_g2 | (block_p2 & block_g1) |
                   (block_p2 & block_p1 & block_g0);

    wire [7:0] sum0 = s5[7:0] + c5[7:0];
    wire [7:0] sum1 = s5[15:8] + c5[15:8] + carry8;
    wire [7:0] sum2 = s5[23:16] + c5[23:16] + carry16;
    wire [7:0] sum3 = s5[31:24] + c5[31:24] + carry24;
    wire signed [31:0] sum = {sum3, sum2, sum1, sum0};

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1) d[i] <= d[i-1];
            y_out <= sum;
        end
    end
endmodule