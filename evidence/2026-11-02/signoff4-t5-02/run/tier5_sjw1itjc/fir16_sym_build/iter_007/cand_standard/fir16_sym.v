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

    localparam signed [9:0] C0 = -10'sd6;
    localparam signed [9:0] C1 = -10'sd20;
    localparam signed [9:0] C2 = -10'sd24;
    localparam signed [9:0] C3 = 10'sd18;
    localparam signed [9:0] C4 = 10'sd110;
    localparam signed [9:0] C5 = 10'sd226;
    localparam signed [9:0] C6 = 10'sd330;
    localparam signed [9:0] C7 = 10'sd390;

    reg signed [15:0] history [0:14];

    reg v1, v2, v3, v4, v5;
    reg signed [26:0] prod1_0, prod1_1, prod1_2, prod1_3;
    reg signed [26:0] prod1_4, prod1_5, prod1_6, prod1_7;
    reg signed [27:0] sum2_0, sum2_1, sum2_2, sum2_3;
    reg signed [23:0] sum3_0;
    reg signed [27:0] sum3_1;
    reg signed [27:0] acc4;
    reg signed [15:0] data5;

    wire ready5 = !v5 || out_ready;
    wire ready4 = !v4 || ready5;
    wire ready3 = !v3 || ready4;
    wire ready2 = !v2 || ready3;
    wire ready1 = !(v1 && v2 && v3 && v4 && v5) || out_ready;

    assign in_ready = ready1;
    assign out_valid = v5;
    assign out_sample = data5;

    wire signed [16:0] current_ext = {in_sample[15], in_sample};
    wire signed [16:0] h0_ext  = {history[14][15], history[14]};
    wire signed [16:0] h1_ext  = {history[0][15], history[0]};
    wire signed [16:0] h2_ext  = {history[1][15], history[1]};
    wire signed [16:0] h3_ext  = {history[2][15], history[2]};
    wire signed [16:0] h4_ext  = {history[3][15], history[3]};
    wire signed [16:0] h5_ext  = {history[4][15], history[4]};
    wire signed [16:0] h6_ext  = {history[5][15], history[5]};
    wire signed [16:0] h7_ext  = {history[6][15], history[6]};
    wire signed [16:0] h8_ext  = {history[7][15], history[7]};
    wire signed [16:0] h9_ext  = {history[8][15], history[8]};
    wire signed [16:0] h10_ext = {history[9][15], history[9]};
    wire signed [16:0] h11_ext = {history[10][15], history[10]};
    wire signed [16:0] h12_ext = {history[11][15], history[11]};
    wire signed [16:0] h13_ext = {history[12][15], history[12]};
    wire signed [16:0] h14_ext = {history[13][15], history[13]};

    wire signed [16:0] pair0 = current_ext + h0_ext;
    wire signed [16:0] pair1 = h1_ext + h14_ext;
    wire signed [16:0] pair2 = h2_ext + h13_ext;
    wire signed [16:0] pair3 = h3_ext + h12_ext;
    wire signed [16:0] pair4 = h4_ext + h11_ext;
    wire signed [16:0] pair5 = h5_ext + h10_ext;
    wire signed [16:0] pair6 = h6_ext + h9_ext;
    wire signed [16:0] pair7 = h7_ext + h8_ext;

    wire signed [26:0] prod0 = pair0 * C0;
    wire signed [26:0] prod1 = pair1 * C1;
    wire signed [26:0] prod2 = pair2 * C2;
    wire signed [26:0] prod3 = pair3 * C3;
    wire signed [26:0] prod4 = pair4 * C4;
    wire signed [26:0] prod5 = pair5 * C5;
    wire signed [26:0] prod6 = pair6 * C6;
    wire signed [26:0] prod7 = pair7 * C7;

    wire signed [24:0] sum3_0_full =
        {{2{sum2_0[23]}}, sum2_0[23:0]} +
        {{2{sum2_1[23]}}, sum2_1[23:0]};
    wire signed [23:0] sum3_0_next = sum3_0_full[23:0];

    wire signed [28:0] sum3_1_full =
        {sum2_2[27], sum2_2} + {sum2_3[27], sum2_3};
    wire signed [27:0] sum3_1_next = sum3_1_full[27:0];

    wire signed [28:0] acc4_full =
        {{5{sum3_0[23]}}, sum3_0} + {sum3_1[27], sum3_1};
    wire signed [27:0] acc4_next = acc4_full[27:0];

    wire signed [16:0] round_increment = {16'b0, acc4[10]};
    wire signed [16:0] rounded = $signed(acc4[27:11]) + round_increment;
    reg signed [15:0] saturated;

    always @(*) begin
        saturated = 16'sd0;
        if (rounded[16] != rounded[15]) begin
            if (rounded[16] == 1'b0)
                saturated = 16'sd32767;
            else
                saturated = -16'sd32768;
        end else begin
            saturated = rounded[15:0];
        end
    end

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
                prod1_0 <= prod0;
                prod1_1 <= prod1;
                prod1_2 <= prod2;
                prod1_3 <= prod3;
                prod1_4 <= prod4;
                prod1_5 <= prod5;
                prod1_6 <= prod6;
                prod1_7 <= prod7;
            end
            if (ready2) begin
                v2 <= v1;
                sum2_0 <= {{1{prod1_0[26]}}, prod1_0} + {{1{prod1_1[26]}}, prod1_1};
                sum2_1 <= {{1{prod1_2[26]}}, prod1_2} + {{1{prod1_3[26]}}, prod1_3};
                sum2_2 <= {{1{prod1_4[26]}}, prod1_4} + {{1{prod1_5[26]}}, prod1_5};
                sum2_3 <= {{1{prod1_6[26]}}, prod1_6} + {{1{prod1_7[26]}}, prod1_7};
            end
            if (ready3) begin
                v3 <= v2;
                sum3_0 <= sum3_0_next;
                sum3_1 <= sum3_1_next;
            end
            if (ready4) begin
                v4 <= v3;
                acc4 <= acc4_next;
            end
            if (ready5) begin
                v5 <= v4;
                data5 <= saturated;
            end
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 5
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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