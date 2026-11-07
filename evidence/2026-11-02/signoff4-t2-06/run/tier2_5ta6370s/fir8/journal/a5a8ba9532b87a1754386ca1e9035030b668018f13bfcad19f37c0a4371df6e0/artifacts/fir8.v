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

    wire signed [31:0] pair0 = prod[0]  + prod[63];
    wire signed [31:0] pair1 = prod[9]  + prod[54];
    wire signed [31:0] pair2 = prod[18] + prod[45];
    wire signed [31:0] pair3 = prod[27] + prod[36];
    wire signed [31:0] sum0 = pair0 + pair1;
    wire signed [31:0] sum1 = pair2 + pair3;
    wire signed [31:0] total = sum0 + sum1;

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