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

    reg signed [15:0] d [0:9];

    wire signed [16:0] sample_sum_0 =
        {d[1][15], d[1]} + {d[8][15], d[8]};
    wire signed [16:0] sample_sum_1 =
        {d[2][15], d[2]} + {d[7][15], d[7]};
    wire signed [16:0] sample_sum_2 =
        {d[3][15], d[3]} + {d[6][15], d[6]};
    wire signed [16:0] sample_sum_3 =
        {d[4][15], d[4]} + {d[5][15], d[5]};

    wire [31:0] p0, p1, p2, p3, p4, p5, p6, p7;

    generate
        if (C0 == C7) begin : g_pair_07
            reg signed [31:0] pair_product;
            always @(posedge clk) begin
                if (rst)
                    pair_product <= 32'sd0;
                else
                    pair_product <= sample_sum_0 * C0;
            end
            assign p0 = pair_product;
            assign p7 = 32'd0;
        end else begin : g_independent_07
            reg signed [31:0] product_0, product_7;
            always @(posedge clk) begin
                if (rst) begin
                    product_0 <= 32'sd0;
                    product_7 <= 32'sd0;
                end else begin
                    product_0 <= d[1] * C0;
                    product_7 <= d[8] * C7;
                end
            end
            assign p0 = product_0;
            assign p7 = product_7;
        end

        if (C1 == C6) begin : g_pair_16
            reg signed [31:0] pair_product;
            always @(posedge clk) begin
                if (rst)
                    pair_product <= 32'sd0;
                else
                    pair_product <= sample_sum_1 * C1;
            end
            assign p1 = pair_product;
            assign p6 = 32'd0;
        end else begin : g_independent_16
            reg signed [31:0] product_1, product_6;
            always @(posedge clk) begin
                if (rst) begin
                    product_1 <= 32'sd0;
                    product_6 <= 32'sd0;
                end else begin
                    product_1 <= d[2] * C1;
                    product_6 <= d[7] * C6;
                end
            end
            assign p1 = product_1;
            assign p6 = product_6;
        end

        if (C2 == C5) begin : g_pair_25
            reg signed [31:0] pair_product;
            always @(posedge clk) begin
                if (rst)
                    pair_product <= 32'sd0;
                else
                    pair_product <= sample_sum_2 * C2;
            end
            assign p2 = pair_product;
            assign p5 = 32'd0;
        end else begin : g_independent_25
            reg signed [31:0] product_2, product_5;
            always @(posedge clk) begin
                if (rst) begin
                    product_2 <= 32'sd0;
                    product_5 <= 32'sd0;
                end else begin
                    product_2 <= d[3] * C2;
                    product_5 <= d[6] * C5;
                end
            end
            assign p2 = product_2;
            assign p5 = product_5;
        end

        if (C3 == C4) begin : g_pair_34
            reg signed [31:0] pair_product;
            always @(posedge clk) begin
                if (rst)
                    pair_product <= 32'sd0;
                else
                    pair_product <= sample_sum_3 * C3;
            end
            assign p3 = pair_product;
            assign p4 = 32'd0;
        end else begin : g_independent_34
            reg signed [31:0] product_3, product_4;
            always @(posedge clk) begin
                if (rst) begin
                    product_3 <= 32'sd0;
                    product_4 <= 32'sd0;
                end else begin
                    product_3 <= d[4] * C3;
                    product_4 <= d[5] * C4;
                end
            end
            assign p3 = product_3;
            assign p4 = product_4;
        end
    endgenerate

    wire [31:0] s1a = p0 ^ p1 ^ p2;
    wire [31:0] c1a = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
    wire [31:0] s1b = p3 ^ p4 ^ p5;
    wire [31:0] c1b = ((p3 & p4) | (p3 & p5) | (p4 & p5)) << 1;

    wire [31:0] s2a = s1a ^ c1a ^ p6;
    wire [31:0] c2a = ((s1a & c1a) | (s1a & p6) | (c1a & p6)) << 1;
    wire [31:0] s2b = s1b ^ c1b ^ p7;
    wire [31:0] c2b = ((s1b & c1b) | (s1b & p7) | (c1b & p7)) << 1;

    wire [31:0] s3a = s2a ^ c2a ^ s2b;
    wire [31:0] c3a = ((s2a & c2a) | (s2a & s2b) | (c2a & s2b)) << 1;

    wire [31:0] s4a = s3a ^ c3a ^ c2b;
    wire [31:0] c4a = ((s3a & c3a) | (s3a & c2b) | (c3a & c2b)) << 1;

    wire [31:0] sum = s4a + c4a;

    integer i;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 10; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 10; i = i + 1)
                d[i] <= d[i-1];
            y_out <= sum;
        end
    end
endmodule