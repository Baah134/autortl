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

    wire signed [31:0] sum_comb;

    generate
        if ((C0 == C7) && (C1 == C6) && (C2 == C5) && (C3 == C4)) begin : gen_symmetric
            wire signed [16:0] pair0;
            wire signed [16:0] pair1;
            wire signed [16:0] pair2;
            wire signed [16:0] pair3;
            wire signed [32:0] full_prod0;
            wire signed [32:0] full_prod1;
            wire signed [32:0] full_prod2;
            wire signed [32:0] full_prod3;
            wire signed [31:0] prod0;
            wire signed [31:0] prod1;
            wire signed [31:0] prod2;
            wire signed [31:0] prod3;
            wire signed [31:0] tree0;
            wire signed [31:0] tree1;

            assign pair0 = $signed(d[0]) + $signed(d[7]);
            assign pair1 = $signed(d[1]) + $signed(d[6]);
            assign pair2 = $signed(d[2]) + $signed(d[5]);
            assign pair3 = $signed(d[3]) + $signed(d[4]);

            assign full_prod0 = pair0 * C0;
            assign full_prod1 = pair1 * C1;
            assign full_prod2 = pair2 * C2;
            assign full_prod3 = pair3 * C3;

            assign prod0 = full_prod0[31:0];
            assign prod1 = full_prod1[31:0];
            assign prod2 = full_prod2[31:0];
            assign prod3 = full_prod3[31:0];

            assign tree0 = prod0 + prod1;
            assign tree1 = prod2 + prod3;
            assign sum_comb = tree0 + tree1;
        end else begin : gen_general
            assign sum_comb = d[0]*C0 + d[1]*C1 + d[2]*C2 + d[3]*C3
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

            sum_pipe0 <= sum_comb;
            sum_pipe1 <= sum_pipe0;
            y_out <= sum_pipe1;
        end
    end
endmodule