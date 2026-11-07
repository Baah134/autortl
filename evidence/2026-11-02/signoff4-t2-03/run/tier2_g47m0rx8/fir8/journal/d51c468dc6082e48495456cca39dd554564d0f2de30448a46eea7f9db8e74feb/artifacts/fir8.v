`timescale 1ns/1ps
// Deliberately naive 8-tap FIR: single-cycle sum of 8 products.
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    output reg  signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;

    reg signed [31:0] q [0:7][0:7];

    genvar k, j;
    generate
        for (k = 0; k < 8; k = k + 1) begin : g_tap
            localparam signed [15:0] COEFF =
                (k == 0) ? C0 :
                (k == 1) ? C1 :
                (k == 2) ? C2 :
                (k == 3) ? C3 :
                (k == 4) ? C4 :
                (k == 5) ? C5 :
                (k == 6) ? C6 : C7;

            wire signed [31:0] product = $signed(x_in) * $signed(COEFF);

            for (j = 0; j <= k; j = j + 1) begin : g_delay
                if (j == 0) begin : g_first
                    always @(posedge clk) begin
                        if (rst)
                            q[k][j] <= 32'sd0;
                        else
                            q[k][j] <= product;
                    end
                end else begin : g_next
                    always @(posedge clk) begin
                        if (rst)
                            q[k][j] <= 32'sd0;
                        else
                            q[k][j] <= q[k][j-1];
                    end
                end
            end
        end
    endgenerate

    wire signed [31:0] s01 = q[0][0] + q[1][1];
    wire signed [31:0] s23 = q[2][2] + q[3][3];
    wire signed [31:0] s45 = q[4][4] + q[5][5];
    wire signed [31:0] s67 = q[6][6] + q[7][7];

    wire signed [31:0] s03 = s01 + s23;
    wire signed [31:0] s47 = s45 + s67;
    wire signed [31:0] sum = s03 + s47;

    always @(posedge clk) begin
        if (rst)
            y_out <= 32'sd0;
        else
            y_out <= sum;
    end
endmodule