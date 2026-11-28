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

    reg signed [15:0] x_sample;
    reg signed [31:0] partial_sum0;
    reg signed [31:0] partial_sum1;
    reg signed [31:0] partial_sum2;
    reg signed [31:0] partial_sum3;
    reg signed [31:0] partial_sum4;
    reg signed [31:0] partial_sum5;
    reg signed [31:0] partial_sum6;

    wire signed [31:0] sample_ext = {{16{x_sample[15]}}, x_sample};
    wire signed [31:0] product0 = sample_ext * C0;
    wire signed [31:0] product1 = sample_ext * C1;
    wire signed [31:0] product2 = sample_ext * C2;
    wire signed [31:0] product3 = sample_ext * C3;
    wire signed [31:0] product4 = sample_ext * C4;
    wire signed [31:0] product5 = sample_ext * C5;
    wire signed [31:0] product6 = sample_ext * C6;
    wire signed [31:0] product7 = sample_ext * C7;

    always @(posedge clk) begin
        if (rst) begin
            x_sample   <= 16'sd0;
            partial_sum0 <= 32'sd0;
            partial_sum1 <= 32'sd0;
            partial_sum2 <= 32'sd0;
            partial_sum3 <= 32'sd0;
            partial_sum4 <= 32'sd0;
            partial_sum5 <= 32'sd0;
            partial_sum6 <= 32'sd0;
            y_out      <= 32'sd0;
        end else begin
            y_out        <= product0 + partial_sum0;
            partial_sum0 <= product1 + partial_sum1;
            partial_sum1 <= product2 + partial_sum2;
            partial_sum2 <= product3 + partial_sum3;
            partial_sum3 <= product4 + partial_sum4;
            partial_sum4 <= product5 + partial_sum5;
            partial_sum5 <= product6 + partial_sum6;
            partial_sum6 <= product7;
            x_sample    <= x_in;
        end
    end
endmodule