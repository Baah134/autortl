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

    reg signed [16:0] pair1 [0:7];
    reg signed [26:0] prod2 [0:7];
    reg signed [28:0] partial3_a, partial3_b;
    reg signed [31:0] rounded4;
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

    wire signed [26:0] prod0 = pair1[0] * C0;
    wire signed [26:0] prod1 = pair1[1] * C1;
    wire signed [26:0] prod2 = pair1[2] * C2;
    wire signed [26:0] prod3 = pair1[3] * C3;
    wire signed [26:0] prod4 = pair1[4] * C4;
    wire signed [26:0] prod5 = pair1[5] * C5;
    wire signed [26:0] prod6 = pair1[6] * C6;
    wire signed [26:0] prod7 = pair1[7] * C7;

    wire signed [28:0] sum_a =
        {{2{prod2[0][26]}}, prod2[0]} +
        {{2{prod2[1][26]}}, prod2[1]} +
        {{2{prod2[2][26]}}, prod2[2]} +
        {{2{prod2[3][26]}}, prod2[3]};
    wire signed [28:0] sum_b =
        {{2{prod2[4][26]}}, prod2[4]} +
        {{2{prod2[5][26]}}, prod2[5]} +
        {{2{prod2[6][26]}}, prod2[6]} +
        {{2{prod2[7][26]}}, prod2[7]};

    wire signed [28:0] acc_wide =
        {{0{partial3_a[28]}}, partial3_a} +
        {{0{partial3_b[28]}}, partial3_b};
    wire signed [27:0] acc = acc_wide[27:0];
    wire signed [31:0] rounded_in =
        ($signed({{4{acc[27]}}, acc}) + 32'sd1024) >>> 11;

    wire signed [15:0] saturated =
        (rounded4 > 32'sd32767) ? 16'sd32767 :
        (rounded4 < -32'sd32768) ? -16'sd32768 :
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
                    pair1[0] <= pair0_in;
                    pair1[1] <= pair1_in;
                    pair1[2] <= pair2_in;
                    pair1[3] <= pair3_in;
                    pair1[4] <= pair4_in;
                    pair1[5] <= pair5_in;
                    pair1[6] <= pair6_in;
                    pair1[7] <= pair7_in;
                end
            end

            if (ready2) begin
                v2 <= v1;
                if (v1) begin
                    prod2[0] <= prod0;
                    prod2[1] <= prod1;
                    prod2[2] <= prod2;
                    prod2[3] <= prod3;
                    prod2[4] <= prod4;
                    prod2[5] <= prod5;
                    prod2[6] <= prod6;
                    prod2[7] <= prod7;
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