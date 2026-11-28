`timescale 1ns/1ps
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    output wire signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;

    reg signed [15:0] d [0:7];
    reg signed [31:0] sum_pipe0;
    reg signed [31:0] sum_pipe1;
    reg signed [31:0] y_out_lo;
    reg signed [31:0] y_out_hi;
    integer i;

    assign y_out = {y_out_hi[31:16], y_out_lo[15:0]};

    wire signed [31:0] sum_value;

    generate
        if ((C0 == 16'sd3)  && (C1 == 16'sd7)  &&
            (C2 == 16'sd12) && (C3 == 16'sd18) &&
            (C4 == 16'sd18) && (C5 == 16'sd12) &&
            (C6 == 16'sd7)  && (C7 == 16'sd3)) begin : g_default_coeffs
            wire signed [16:0] pair0 = d[0] + d[7];
            wire signed [16:0] pair1 = d[1] + d[6];
            wire signed [16:0] pair2 = d[2] + d[5];
            wire signed [16:0] pair3 = d[3] + d[4];

            wire signed [31:0] wide0 = {{15{pair0[16]}}, pair0};
            wire signed [31:0] wide1 = {{15{pair1[16]}}, pair1};
            wire signed [31:0] wide2 = {{15{pair2[16]}}, pair2};
            wire signed [31:0] wide3 = {{15{pair3[16]}}, pair3};

            wire signed [31:0] term0 = (wide0 <<< 1) + wide0;
            wire signed [31:0] term1 = (wide1 <<< 3) - wide1;
            wire signed [31:0] term2 = (wide2 <<< 3) + (wide2 <<< 2);
            wire signed [31:0] term3 = (wide3 <<< 4) + (wide3 <<< 1);

            assign sum_value = (term0 + term1) + (term2 + term3);
        end else begin : g_other_coeffs
            assign sum_value = d[0]*C0 + d[1]*C1 + d[2]*C2 + d[3]*C3
                             + d[4]*C4 + d[5]*C5 + d[6]*C6 + d[7]*C7;
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            sum_pipe0 <= 32'sd0;
            sum_pipe1 <= 32'sd0;
            y_out_lo <= 32'sd0;
            y_out_hi <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];

            sum_pipe0 <= sum_value;
            sum_pipe1 <= sum_pipe0;
            y_out_lo <= sum_pipe1;
            y_out_hi <= sum_pipe1;
        end
    end
endmodule