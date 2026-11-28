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
    reg signed [31:0] sum_pipe0;
    reg signed [31:0] sum_pipe1;
    integer i;

    wire signed [31:0] sum_next;

    generate
        if ((C0 == 16'd3) && (C1 == 16'd7) &&
            (C2 == 16'd12) && (C3 == 16'd18) &&
            (C4 == 16'd18) && (C5 == 16'd12) &&
            (C6 == 16'd7) && (C7 == 16'd3)) begin : default_coefficients
            wire signed [16:0] pair0;
            wire signed [16:0] pair1;
            wire signed [16:0] pair2;
            wire signed [16:0] pair3;
            wire signed [31:0] pair0_ext;
            wire signed [31:0] pair1_ext;
            wire signed [31:0] pair2_ext;
            wire signed [31:0] pair3_ext;
            wire signed [31:0] mult3;
            wire signed [31:0] mult7;
            wire signed [31:0] mult12;
            wire signed [31:0] mult18;

            assign pair0 = $signed({d[0][15], d[0]}) +
                           $signed({d[7][15], d[7]});
            assign pair1 = $signed({d[1][15], d[1]}) +
                           $signed({d[6][15], d[6]});
            assign pair2 = $signed({d[2][15], d[2]}) +
                           $signed({d[5][15], d[5]});
            assign pair3 = $signed({d[3][15], d[3]}) +
                           $signed({d[4][15], d[4]});

            assign pair0_ext = {{15{pair0[16]}}, pair0};
            assign pair1_ext = {{15{pair1[16]}}, pair1};
            assign pair2_ext = {{15{pair2[16]}}, pair2};
            assign pair3_ext = {{15{pair3[16]}}, pair3};

            assign mult3  = (pair0_ext <<< 1) + pair0_ext;
            assign mult7  = (pair1_ext <<< 3) - pair1_ext;
            assign mult12 = (pair2_ext <<< 3) + (pair2_ext <<< 2);
            assign mult18 = (pair3_ext <<< 4) + (pair3_ext <<< 1);

            assign sum_next = (mult3 + mult7) + (mult12 + mult18);
        end else begin : other_coefficients
            assign sum_next = d[0]*C0 + d[1]*C1 + d[2]*C2 + d[3]*C3
                            + d[4]*C4 + d[5]*C5 + d[6]*C6 + d[7]*C7;
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            sum_pipe0 <= 32'sd0;
            sum_pipe1 <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];

            sum_pipe0 <= sum_next;
            sum_pipe1 <= sum_pipe0;
            y_out <= sum_pipe1;
        end
    end
endmodule