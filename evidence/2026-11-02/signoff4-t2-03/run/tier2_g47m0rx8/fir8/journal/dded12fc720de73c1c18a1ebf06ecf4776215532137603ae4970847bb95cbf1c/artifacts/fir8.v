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
        reg signed [31:0] t0, t1, t2, t3, t4, t5, t6, t7;
        reg signed [31:0] t8, t9, t10, t11, t12, t13, t14, t15;
        reg signed [31:0] l0, l1, l2, l3, l4, l5, l6, l7;
        reg signed [31:0] m0, m1, m2, m3;
        reg signed [31:0] n0, n1;
        begin
            ax = {{16{a[15]}}, a};

            t0  = b[0]  ? (ax << 0)  : 32'sd0;
            t1  = b[1]  ? (ax << 1)  : 32'sd0;
            t2  = b[2]  ? (ax << 2)  : 32'sd0;
            t3  = b[3]  ? (ax << 3)  : 32'sd0;
            t4  = b[4]  ? (ax << 4)  : 32'sd0;
            t5  = b[5]  ? (ax << 5)  : 32'sd0;
            t6  = b[6]  ? (ax << 6)  : 32'sd0;
            t7  = b[7]  ? (ax << 7)  : 32'sd0;
            t8  = b[8]  ? (ax << 8)  : 32'sd0;
            t9  = b[9]  ? (ax << 9)  : 32'sd0;
            t10 = b[10] ? (ax << 10) : 32'sd0;
            t11 = b[11] ? (ax << 11) : 32'sd0;
            t12 = b[12] ? (ax << 12) : 32'sd0;
            t13 = b[13] ? (ax << 13) : 32'sd0;
            t14 = b[14] ? (ax << 14) : 32'sd0;
            t15 = b[15] ? -(ax << 15) : 32'sd0;

            l0 = t0 + t1;
            l1 = t2 + t3;
            l2 = t4 + t5;
            l3 = t6 + t7;
            l4 = t8 + t9;
            l5 = t10 + t11;
            l6 = t12 + t13;
            l7 = t14 + t15;

            m0 = l0 + l1;
            m1 = l2 + l3;
            m2 = l4 + l5;
            m3 = l6 + l7;

            n0 = m0 + m1;
            n1 = m2 + m3;

            mul_shift_add = n0 + n1;
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

    wire signed [31:0] sum = s5 + c5;

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