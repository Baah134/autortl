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
    reg signed [19:0] product0_reg;
    reg signed [21:0] product1_reg;
    reg signed [21:0] product2_reg;
    reg signed [21:0] product3_reg;
    reg signed [23:0] product4_reg;
    reg signed [24:0] product5_reg;
    reg signed [25:0] product6_reg;
    reg signed [25:0] product7_reg;
    reg signed [23:0] partial3_a;
    reg signed [27:0] partial3_b;
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

    localparam signed [9:0] C0 = -10'sd6;
    localparam signed [9:0] C1 = -10'sd20;
    localparam signed [9:0] C2 = -10'sd24;
    localparam signed [9:0] C3 = 10'sd18;
    localparam signed [9:0] C4 = 10'sd110;
    localparam signed [9:0] C5 = 10'sd226;
    localparam signed [9:0] C6 = 10'sd330;
    localparam signed [9:0] C7 = 10'sd390;

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

    wire signed [19:0] pair0_ext = {{3{pair_reg[0][16]}}, pair_reg[0]};
    wire signed [21:0] pair1_ext = {{5{pair_reg[1][16]}}, pair_reg[1]};
    wire signed [21:0] pair2_ext = {{5{pair_reg[2][16]}}, pair_reg[2]};
    wire signed [21:0] pair3_ext = {{5{pair_reg[3][16]}}, pair_reg[3]};
    wire signed [23:0] pair4_ext = {{7{pair_reg[4][16]}}, pair_reg[4]};
    wire signed [24:0] pair5_ext = {{8{pair_reg[5][16]}}, pair_reg[5]};
    wire signed [25:0] pair6_ext = {{9{pair_reg[6][16]}}, pair_reg[6]};
    wire signed [25:0] pair7_ext = {{9{pair_reg[7][16]}}, pair_reg[7]};

    wire signed [19:0] coeff0_ext = {{10{C0[9]}}, C0};
    wire signed [21:0] coeff1_ext = {{12{C1[9]}}, C1};
    wire signed [21:0] coeff2_ext = {{12{C2[9]}}, C2};
    wire signed [21:0] coeff3_ext = {{12{C3[9]}}, C3};
    wire signed [23:0] coeff4_ext = {{14{C4[9]}}, C4};
    wire signed [24:0] coeff5_ext = {{15{C5[9]}}, C5};
    wire signed [25:0] coeff6_ext = {{16{C6[9]}}, C6};
    wire signed [25:0] coeff7_ext = {{16{C7[9]}}, C7};

    wire signed [19:0] product0 = pair0_ext * coeff0_ext;
    wire signed [21:0] product1 = pair1_ext * coeff1_ext;
    wire signed [21:0] product2 = pair2_ext * coeff2_ext;
    wire signed [21:0] product3 = pair3_ext * coeff3_ext;
    wire signed [23:0] product4 = pair4_ext * coeff4_ext;
    wire signed [24:0] product5 = pair5_ext * coeff5_ext;
    wire signed [25:0] product6 = pair6_ext * coeff6_ext;
    wire signed [25:0] product7 = pair7_ext * coeff7_ext;

    wire signed [21:0] sum_a_pair01 =
        {{2{product0_reg[19]}}, product0_reg} +
        {{1{product1_reg[21]}}, product1_reg};
    wire signed [22:0] sum_a_pair23 =
        {product2_reg[21], product2_reg} +
        {product3_reg[21], product3_reg};
    wire signed [23:0] sum_a =
        {{2{sum_a_pair01[21]}}, sum_a_pair01} +
        {{1{sum_a_pair23[22]}}, sum_a_pair23};

    wire signed [25:0] sum_b_pair45 =
        {{2{product4_reg[23]}}, product4_reg} +
        {product5_reg[24], product5_reg};
    wire signed [26:0] sum_b_pair67 =
        {product6_reg[25], product6_reg} +
        {product7_reg[25], product7_reg};
    wire signed [27:0] sum_b =
        {{2{sum_b_pair45[25]}}, sum_b_pair45} +
        {sum_b_pair67[26], sum_b_pair67};

    wire signed [27:0] acc_full =
        {{4{partial3_a[23]}}, partial3_a} + partial3_b;
    wire signed [31:0] rounded_in =
        ($signed({{4{acc_full[27]}}, acc_full}) + 32'sd1024) >>> 11;

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
                    product0_reg <= product0;
                    product1_reg <= product1;
                    product2_reg <= product2;
                    product3_reg <= product3;
                    product4_reg <= product4;
                    product5_reg <= product5;
                    product6_reg <= product6;
                    product7_reg <= product7;
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