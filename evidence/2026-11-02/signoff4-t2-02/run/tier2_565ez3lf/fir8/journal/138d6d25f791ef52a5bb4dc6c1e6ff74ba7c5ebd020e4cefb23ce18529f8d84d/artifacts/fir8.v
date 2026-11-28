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

    generate
        if ((C0 == 16'sd3)  && (C1 == 16'sd7)  &&
            (C2 == 16'sd12) && (C3 == 16'sd18) &&
            (C4 == 16'sd18) && (C5 == 16'sd12) &&
            (C6 == 16'sd7)  && (C7 == 16'sd3)) begin : default_coefficients

            reg signed [22:0] acc [0:6];

            wire signed [22:0] p0 = d[0] * C0;
            wire signed [22:0] p1 = d[0] * C1;
            wire signed [22:0] p2 = d[0] * C2;
            wire signed [22:0] p3 = d[0] * C3;
            wire signed [22:0] p4 = d[0] * C4;
            wire signed [22:0] p5 = d[0] * C5;
            wire signed [22:0] p6 = d[0] * C6;
            wire signed [22:0] p7 = d[0] * C7;

            always @(posedge clk) begin
                if (rst) begin
                    for (i = 0; i < 8; i = i + 1)
                        d[i] <= 16'sd0;
                    for (i = 0; i < 7; i = i + 1)
                        acc[i] <= 23'sd0;
                    y_out <= 32'sd0;
                end else begin
                    d[0] <= x_in;
                    for (i = 1; i < 8; i = i + 1)
                        d[i] <= d[i-1];

                    y_out <= {{9{(p0 + acc[0])[22]}}, (p0 + acc[0])};
                    acc[0] <= p1 + acc[1];
                    acc[1] <= p2 + acc[2];
                    acc[2] <= p3 + acc[3];
                    acc[3] <= p4 + acc[4];
                    acc[4] <= p5 + acc[5];
                    acc[5] <= p6 + acc[6];
                    acc[6] <= p7;
                end
            end
        end else begin : general_coefficients
            reg signed [31:0] acc [0:6];

            wire signed [31:0] p0 = d[0] * C0;
            wire signed [31:0] p1 = d[0] * C1;
            wire signed [31:0] p2 = d[0] * C2;
            wire signed [31:0] p3 = d[0] * C3;
            wire signed [31:0] p4 = d[0] * C4;
            wire signed [31:0] p5 = d[0] * C5;
            wire signed [31:0] p6 = d[0] * C6;
            wire signed [31:0] p7 = d[0] * C7;

            always @(posedge clk) begin
                if (rst) begin
                    for (i = 0; i < 8; i = i + 1)
                        d[i] <= 16'sd0;
                    for (i = 0; i < 7; i = i + 1)
                        acc[i] <= 32'sd0;
                    y_out <= 32'sd0;
                end else begin
                    d[0] <= x_in;
                    for (i = 1; i < 8; i = i + 1)
                        d[i] <= d[i-1];

                    y_out <= p0 + acc[0];
                    acc[0] <= p1 + acc[1];
                    acc[1] <= p2 + acc[2];
                    acc[2] <= p3 + acc[3];
                    acc[3] <= p4 + acc[4];
                    acc[4] <= p5 + acc[5];
                    acc[5] <= p6 + acc[6];
                    acc[6] <= p7;
                end
            end
        end
    endgenerate
endmodule