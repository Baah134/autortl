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
    reg signed [31:0] y_reg;
    wire signed [31:0] sum_value;
    integer i;

    assign y_out = y_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];
        end
    end

    generate
        if ((C0 == C7) && (C1 == C6) && (C2 == C5) && (C3 == C4)) begin : symmetric_coefficients
            wire signed [16:0] pair0;
            wire signed [16:0] pair1;
            wire signed [16:0] pair2;
            wire signed [16:0] pair3;
            wire signed [31:0] p0;
            wire signed [31:0] p1;
            wire signed [31:0] p2;
            wire signed [31:0] p3;
            wire signed [31:0] sum01;
            wire signed [31:0] sum23;

            assign pair0 = {d[0][15], d[0]} + {d[7][15], d[7]};
            assign pair1 = {d[1][15], d[1]} + {d[6][15], d[6]};
            assign pair2 = {d[2][15], d[2]} + {d[5][15], d[5]};
            assign pair3 = {d[3][15], d[3]} + {d[4][15], d[4]};

            assign p0 = $signed(pair0) * $signed(C0);
            assign p1 = $signed(pair1) * $signed(C1);
            assign p2 = $signed(pair2) * $signed(C2);
            assign p3 = $signed(pair3) * $signed(C3);
            assign sum01 = p0 + p1;
            assign sum23 = p2 + p3;
            assign sum_value = sum01 + sum23;
        end else begin : general_coefficients
            wire signed [31:0] p0;
            wire signed [31:0] p1;
            wire signed [31:0] p2;
            wire signed [31:0] p3;
            wire signed [31:0] p4;
            wire signed [31:0] p5;
            wire signed [31:0] p6;
            wire signed [31:0] p7;
            wire signed [31:0] sum01;
            wire signed [31:0] sum23;
            wire signed [31:0] sum45;
            wire signed [31:0] sum67;
            wire signed [31:0] sum0123;
            wire signed [31:0] sum4567;

            assign p0 = d[0] * C0;
            assign p1 = d[1] * C1;
            assign p2 = d[2] * C2;
            assign p3 = d[3] * C3;
            assign p4 = d[4] * C4;
            assign p5 = d[5] * C5;
            assign p6 = d[6] * C6;
            assign p7 = d[7] * C7;

            assign sum01 = p0 + p1;
            assign sum23 = p2 + p3;
            assign sum45 = p4 + p5;
            assign sum67 = p6 + p7;
            assign sum0123 = sum01 + sum23;
            assign sum4567 = sum45 + sum67;
            assign sum_value = sum0123 + sum4567;
        end
    endgenerate

    always @(posedge clk) begin
        if (rst)
            y_reg <= 32'sd0;
        else
            y_reg <= sum_value;
    end
endmodule