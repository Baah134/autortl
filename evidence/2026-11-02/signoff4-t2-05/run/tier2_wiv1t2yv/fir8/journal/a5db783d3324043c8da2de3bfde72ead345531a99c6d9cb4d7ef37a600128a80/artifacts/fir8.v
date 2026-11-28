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

    wire signed [31:0] pair0_product;
    wire signed [31:0] pair1_product;
    wire signed [31:0] pair2_product;
    wire signed [31:0] pair3_product;

    generate
        if (C0 == C7) begin : g_pair0_equal
            wire signed [16:0] sample_sum =
                {d[0][15], d[0]} + {d[7][15], d[7]};
            wire signed [31:0] sample_ext =
                {{15{sample_sum[16]}}, sample_sum};
            if (C0 == 16'sd3) begin : g_coeff3
                assign pair0_product = (sample_ext <<< 1) + sample_ext;
            end else begin : g_coeff_generic
                assign pair0_product = sample_sum * C0;
            end
        end else begin : g_pair0_unequal
            wire signed [31:0] product0 = d[0] * C0;
            wire signed [31:0] product7 = d[7] * C7;
            assign pair0_product = product0 + product7;
        end

        if (C1 == C6) begin : g_pair1_equal
            wire signed [16:0] sample_sum =
                {d[1][15], d[1]} + {d[6][15], d[6]};
            wire signed [31:0] sample_ext =
                {{15{sample_sum[16]}}, sample_sum};
            if (C1 == 16'sd7) begin : g_coeff7
                assign pair1_product = (sample_ext <<< 3) - sample_ext;
            end else begin : g_coeff_generic
                assign pair1_product = sample_sum * C1;
            end
        end else begin : g_pair1_unequal
            wire signed [31:0] product1 = d[1] * C1;
            wire signed [31:0] product6 = d[6] * C6;
            assign pair1_product = product1 + product6;
        end

        if (C2 == C5) begin : g_pair2_equal
            wire signed [16:0] sample_sum =
                {d[2][15], d[2]} + {d[5][15], d[5]};
            wire signed [31:0] sample_ext =
                {{15{sample_sum[16]}}, sample_sum};
            if (C2 == 16'sd12) begin : g_coeff12
                assign pair2_product = (sample_ext <<< 3) + (sample_ext <<< 2);
            end else begin : g_coeff_generic
                assign pair2_product = sample_sum * C2;
            end
        end else begin : g_pair2_unequal
            wire signed [31:0] product2 = d[2] * C2;
            wire signed [31:0] product5 = d[5] * C5;
            assign pair2_product = product2 + product5;
        end

        if (C3 == C4) begin : g_pair3_equal
            wire signed [16:0] sample_sum =
                {d[3][15], d[3]} + {d[4][15], d[4]};
            wire signed [31:0] sample_ext =
                {{15{sample_sum[16]}}, sample_sum};
            if (C3 == 16'sd18) begin : g_coeff18
                assign pair3_product = (sample_ext <<< 4) + (sample_ext <<< 1);
            end else begin : g_coeff_generic
                assign pair3_product = sample_sum * C3;
            end
        end else begin : g_pair3_unequal
            wire signed [31:0] product3 = d[3] * C3;
            wire signed [31:0] product4 = d[4] * C4;
            assign pair3_product = product3 + product4;
        end
    endgenerate

    wire signed [31:0] sum01 = pair0_product + pair1_product;
    wire signed [31:0] sum23 = pair2_product + pair3_product;
    wire signed [31:0] total_sum = sum01 + sum23;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1)
                d[i] <= d[i-1];
            y_out <= total_sum;
        end
    end
endmodule