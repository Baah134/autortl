`timescale 1ns/1ps
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    (* IOB = "TRUE" *) output reg signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;

    reg signed [15:0] d [0:7];
    reg signed [31:0] sum_pipe0_a;
    reg signed [31:0] sum_pipe0_b;
    reg signed [31:0] sum_pipe1;
    integer i;

    wire signed [16:0] pair0 = {d[0][15], d[0]} + {d[7][15], d[7]};
    wire signed [16:0] pair1 = {d[1][15], d[1]} + {d[6][15], d[6]};
    wire signed [16:0] pair2 = {d[2][15], d[2]} + {d[5][15], d[5]};
    wire signed [16:0] pair3 = {d[3][15], d[3]} + {d[4][15], d[4]};

    wire signed [31:0] pair0_ext = {{15{pair0[16]}}, pair0};
    wire signed [31:0] pair1_ext = {{15{pair1[16]}}, pair1};
    wire signed [31:0] pair2_ext = {{15{pair2[16]}}, pair2};
    wire signed [31:0] pair3_ext = {{15{pair3[16]}}, pair3};

    wire signed [31:0] c0_ext = {{16{C0[15]}}, C0};
    wire signed [31:0] c1_ext = {{16{C1[15]}}, C1};
    wire signed [31:0] c2_ext = {{16{C2[15]}}, C2};
    wire signed [31:0] c3_ext = {{16{C3[15]}}, C3};
    wire signed [31:0] c4_ext = {{16{C4[15]}}, C4};
    wire signed [31:0] c5_ext = {{16{C5[15]}}, C5};
    wire signed [31:0] c6_ext = {{16{C6[15]}}, C6};
    wire signed [31:0] c7_ext = {{16{C7[15]}}, C7};

    wire signed [31:0] p0;
    wire signed [31:0] p1;
    wire signed [31:0] p2;
    wire signed [31:0] p3;
    wire signed [31:0] p4;
    wire signed [31:0] p5;
    wire signed [31:0] p6;
    wire signed [31:0] p7;
    wire signed [31:0] sum_a;
    wire signed [31:0] sum_b;

    generate
        if ((C0 == C7) && (C1 == C6) && (C2 == C5) && (C3 == C4)) begin : symmetric_coefficients
            assign p0 = pair0_ext * c0_ext;
            assign p1 = pair1_ext * c1_ext;
            assign p2 = pair2_ext * c2_ext;
            assign p3 = pair3_ext * c3_ext;
            assign p4 = 32'sd0;
            assign p5 = 32'sd0;
            assign p6 = 32'sd0;
            assign p7 = 32'sd0;
            assign sum_a = p0 + p1;
            assign sum_b = p2 + p3;
        end else begin : general_coefficients
            wire signed [31:0] x0_ext = {{16{d[0][15]}}, d[0]};
            wire signed [31:0] x1_ext = {{16{d[1][15]}}, d[1]};
            wire signed [31:0] x2_ext = {{16{d[2][15]}}, d[2]};
            wire signed [31:0] x3_ext = {{16{d[3][15]}}, d[3]};
            wire signed [31:0] x4_ext = {{16{d[4][15]}}, d[4]};
            wire signed [31:0] x5_ext = {{16{d[5][15]}}, d[5]};
            wire signed [31:0] x6_ext = {{16{d[6][15]}}, d[6]};
            wire signed [31:0] x7_ext = {{16{d[7][15]}}, d[7]};

            assign p0 = x0_ext * c0_ext;
            assign p1 = x1_ext * c1_ext;
            assign p2 = x2_ext * c2_ext;
            assign p3 = x3_ext * c3_ext;
            assign p4 = x4_ext * c4_ext;
            assign p5 = x5_ext * c5_ext;
            assign p6 = x6_ext * c6_ext;
            assign p7 = x7_ext * c7_ext;
            assign sum_a = (p0 + p1) + (p2 + p3);
            assign sum_b = (p4 + p5) + (p6 + p7);
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            sum_pipe0_a <= 32'sd0;
            sum_pipe0_b <= 32'sd0;
            sum_pipe1 <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];

            sum_pipe0_a <= sum_a;
            sum_pipe0_b <= sum_b;
            sum_pipe1 <= sum_pipe0_a + sum_pipe0_b;
            y_out <= sum_pipe1;
        end
    end
endmodule