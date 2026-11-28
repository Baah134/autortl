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

            wire [31:0] a1 = (e0 << 1);
            wire [31:0] b1 = e0;
            wire [31:0] c1 = (e1 << 3);
            wire [31:0] d1 = ~e1;
            wire [31:0] e1_corr = 32'd1;
            wire [31:0] f1 = (e2 << 3);
            wire [31:0] g1 = (e2 << 2);
            wire [31:0] h1 = (e3 << 4);
            wire [31:0] i1 = (e3 << 1);

            wire [31:0] m1_s = a1 ^ b1 ^ c1;
            wire [31:0] m1_m = (a1 & b1) | (a1 & c1) | (b1 & c1);
            wire [31:0] m1_c = {m1_m[30:0], 1'b0};

            wire [31:0] m2_s = d1 ^ e1_corr ^ f1;
            wire [31:0] m2_m = (d1 & e1_corr) | (d1 & f1) | (e1_corr & f1);
            wire [31:0] m2_c = {m2_m[30:0], 1'b0};

            wire [31:0] m3_s = g1 ^ h1 ^ i1;
            wire [31:0] m3_m = (g1 & h1) | (g1 & i1) | (h1 & i1);
            wire [31:0] m3_c = {m3_m[30:0], 1'b0};

            wire [31:0] n1_s = m1_s ^ m1_c ^ m2_s;
            wire [31:0] n1_m = (m1_s & m1_c) | (m1_s & m2_s) | (m1_c & m2_s);
            wire [31:0] n1_c = {n1_m[30:0], 1'b0};

            wire [31:0] n2_s = m2_c ^ m3_s ^ m3_c;
            wire [31:0] n2_m = (m2_c & m3_s) | (m2_c & m3_c) | (m3_s & m3_c);
            wire [31:0] n2_c = {n2_m[30:0], 1'b0};

            wire [31:0] p1_s = n1_s ^ n1_c ^ n2_s;
            wire [31:0] p1_m = (n1_s & n1_c) | (n1_s & n2_s) | (n1_c & n2_s);
            wire [31:0] p1_c = {p1_m[30:0], 1'b0};

            wire [31:0] q1_s = p1_s ^ p1_c ^ n2_c;
            wire [31:0] q1_m = (p1_s & p1_c) | (p1_s & n2_c) | (p1_c & n2_c);
            wire [31:0] q1_c = {q1_m[30:0], 1'b0};

            assign total = q1_s + q1_c;
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

            wire signed [31:0] pair0 = p0 + p1;
            wire signed [31:0] pair1 = p2 + p3;

            assign total = pair0 + pair1;
        end else begin : general
            wire signed [31:0] p0 = d[0] * C0;
            wire signed [31:0] p1 = d[1] * C1;
            wire signed [31:0] p2 = d[2] * C2;
            wire signed [31:0] p3 = d[3] * C3;
            wire signed [31:0] p4 = d[4] * C4;
            wire signed [31:0] p5 = d[5] * C5;
            wire signed [31:0] p6 = d[6] * C6;
            wire signed [31:0] p7 = d[7] * C7;

            wire signed [31:0] pair0 = p0 + p1;
            wire signed [31:0] pair1 = p2 + p3;
            wire signed [31:0] pair2 = p4 + p5;
            wire signed [31:0] pair3 = p6 + p7;

            wire signed [31:0] sum0 = pair0 + pair1;
            wire signed [31:0] sum1 = pair2 + pair3;

            assign total = sum0 + sum1;
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