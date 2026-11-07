`timescale 1ns/1ps
// @latency 5
module fir16_sym_core (
    input wire clk,
    input wire rst,
    input wire signed [15:0] in_sample,
    input wire in_valid,
    output wire in_ready,
    output wire signed [15:0] out_sample,
    output wire out_valid,
    input wire out_ready
);

    reg signed [15:0] history [0:14];
    reg v1, v2, v3, v4, v5;

    reg signed [16:0] pair_reg [0:7];
    reg signed [18:0] product_reg0;
    reg signed [20:0] product_reg1;
    reg signed [20:0] product_reg2;
    reg signed [19:0] product_reg3;
    reg signed [22:0] product_reg4;
    reg signed [23:0] product_reg5;
    reg signed [24:0] product_reg6;
    reg signed [24:0] product_reg7;
    reg signed [22:0] partial3_a;
    reg signed [26:0] partial3_b;
    reg signed [16:0] rounded4;
    reg signed [15:0] data5;

    wire ready5 = !v5 || out_ready;
    wire ready4 = !v4 || ready5;
    wire ready3 = !v3 || ready4;
    wire ready2 = !v2 || ready3;
    wire ready1 = !v1 || ready2;

    assign in_ready = ready1;
    assign out_valid = v5;
    assign out_sample = data5;

    localparam signed [8:0] C0 = -9'sd3;
    localparam signed [8:0] C1 = -9'sd10;
    localparam signed [8:0] C2 = -9'sd12;
    localparam signed [8:0] C3 = 9'sd9;
    localparam signed [8:0] C4 = 9'sd55;
    localparam signed [8:0] C5 = 9'sd113;
    localparam signed [8:0] C6 = 9'sd165;
    localparam signed [8:0] C7 = 9'sd195;

    wire signed [16:0] pair0_in =
        {in_sample[15], in_sample} + {history[14][15], history[14]};
    wire signed [16:0] pair1_in =
        {history[0][15], history[0]} + {history[13][15], history[13]};
    wire signed [16:0] pair2_in =
        {history[1][15], history[1]} + {history[12][15], history[12]};
    wire signed [16:0] pair3_in =
        {history[2][15], history[2]} + {history[11][15], history[11]};
    wire signed [16:0] pair4_in =
        {history[3][15], history[3]} + {history[10][15], history[10]};
    wire signed [16:0] pair5_in =
        {history[4][15], history[4]} + {history[9][15], history[9]};
    wire signed [16:0] pair6_in =
        {history[5][15], history[5]} + {history[8][15], history[8]};
    wire signed [16:0] pair7_in =
        {history[6][15], history[6]} + {history[7][15], history[7]};

    wire signed [18:0] product0 = pair_reg[0] * C0;
    wire signed [20:0] product1 = pair_reg[1] * C1;
    wire signed [20:0] product2 = pair_reg[2] * C2;
    wire signed [19:0] product3 = pair_reg[3] * C3;
    wire signed [22:0] product4 = pair_reg[4] * C4;
    wire signed [23:0] product5 = pair_reg[5] * C5;
    wire signed [24:0] product6 = pair_reg[6] * C6;
    wire signed [24:0] product7 = pair_reg[7] * C7;

    wire signed [20:0] sum_a_pair01 =
        {{2{product_reg0[18]}}, product_reg0} +
        {product_reg1[20], product_reg1};
    wire signed [21:0] sum_a_pair23 =
        {product_reg2[20], product_reg2} +
        {{2{product_reg3[19]}}, product_reg3};
    wire signed [22:0] sum_a =
        {{2{sum_a_pair01[20]}}, sum_a_pair01} +
        {sum_a_pair23[21], sum_a_pair23};

    wire signed [24:0] sum_b_pair45 =
        {{2{product_reg4[22]}}, product_reg4} +
        {product_reg5[23], product_reg5};
    wire signed [25:0] sum_b_pair67 =
        {product_reg6[24], product_reg6} +
        {product_reg7[24], product_reg7};
    wire signed [26:0] sum_b =
        {{2{sum_b_pair45[24]}}, sum_b_pair45} +
        {sum_b_pair67[25], sum_b_pair67};

    wire signed [26:0] acc_half =
        {{4{partial3_a[22]}}, partial3_a} + partial3_b;
    wire signed [16:0] rounded_in =
        ($signed(acc_half + 27'sd512)) >>> 10;

    wire signed [15:0] saturated =
        (rounded4 > 17'sd32767) ? 16'sd32767 :
        (rounded4 < -17'sd32768) ? -16'sd32768 :
        rounded4[15:0];

    integer i;
    always @(posedge clk) begin
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            v4 <= 1'b0;
            v5 <= 1'b0;
            for (i = 0; i < 15; i = i + 1)
                history[i] <= 16'sd0;
        end else begin
            if (in_valid && in_ready) begin
                history[0] <= in_sample;
                for (i = 1; i < 15; i = i + 1)
                    history[i] <= history[i-1];
            end

            if (ready1) begin
                v1 <= in_valid;
                if (in_valid) begin
                    pair_reg[0] <= pair0_in;
                    pair_reg[1] <= pair1_in;
                    pair_reg[2] <= pair2_in;
                    pair_reg[3] <= pair3_in;
                    pair_reg[4] <= pair4_in;
                    pair_reg[5] <= pair5_in;
                    pair_reg[6] <= pair6_in;
                    pair_reg[7] <= pair7_in;
                end
            end

            if (ready2) begin
                v2 <= v1;
                if (v1) begin
                    product_reg0 <= product0;
                    product_reg1 <= product1;
                    product_reg2 <= product2;
                    product_reg3 <= product3;
                    product_reg4 <= product4;
                    product_reg5 <= product5;
                    product_reg6 <= product6;
                    product_reg7 <= product7;
                end
            end

            if (ready3) begin
                v3 <= v2;
                if (v2) begin
                    partial3_a <= sum_a;
                    partial3_b <= sum_b;
                end
            end

            if (ready4) begin
                v4 <= v3;
                if (v3)
                    rounded4 <= rounded_in;
            end

            if (ready5) begin
                v5 <= v4;
                if (v4)
                    data5 <= saturated;
            end
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 5
module fir16_sym (
    input wire clk,
    input wire rst,
    input wire signed [15:0] in_sample,
    input wire in_valid,
    output wire in_ready,
    output wire signed [15:0] out_sample,
    output wire out_valid,
    input wire out_ready
);
    fir16_sym_core u_fir16_sym_core (
        .clk(clk),
        .rst(rst),
        .in_sample(in_sample),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_sample(out_sample),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule