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

    reg v1, v2, v3, v4, v5;
    reg signed [15:0] history [0:14];
    reg signed [16:0] pair1 [0:7];
    reg signed [27:0] partial2, partial3, accum4;
    reg signed [15:0] d5;

    wire ready5;
    wire ready4;
    wire ready3;
    wire ready2;
    wire ready1;

    assign ready5 = !v5 || out_ready;
    assign ready4 = !v4 || ready5;
    assign ready3 = !v3 || ready4;
    assign ready2 = !v2 || ready3;
    assign ready1 = !v1 || ready2;

    assign in_ready = ready1;
    assign out_valid = v5;
    assign out_sample = d5;

    wire signed [26:0] p0 = $signed(pair1[0]) * -27'sd6;
    wire signed [26:0] p1 = $signed(pair1[1]) * -27'sd20;
    wire signed [26:0] p2 = $signed(pair1[2]) * -27'sd24;
    wire signed [26:0] p3 = $signed(pair1[3]) * 27'sd18;
    wire signed [26:0] p4 = $signed(pair1[4]) * 27'sd110;
    wire signed [26:0] p5 = $signed(pair1[5]) * 27'sd226;
    wire signed [26:0] p6 = $signed(pair1[6]) * 27'sd330;
    wire signed [26:0] p7 = $signed(pair1[7]) * 27'sd390;

    wire signed [27:0] p0_ext = {p0[26], p0};
    wire signed [27:0] p1_ext = {p1[26], p1};
    wire signed [27:0] p2_ext = {p2[26], p2};
    wire signed [27:0] p3_ext = {p3[26], p3};
    wire signed [27:0] p4_ext = {p4[26], p4};
    wire signed [27:0] p5_ext = {p5[26], p5};
    wire signed [27:0] p6_ext = {p6[26], p6};
    wire signed [27:0] p7_ext = {p7[26], p7};

    wire signed [27:0] group2 =
        (p0_ext + p1_ext) + (p2_ext + p3_ext);
    wire signed [27:0] group3 =
        (p4_ext + p5_ext) + (p6_ext + p7_ext);

    wire signed [27:0] rounded5 = (accum4 + 28'sd1024) >>> 11;
    wire signed [15:0] result5 =
        (rounded5 > 28'sd32767) ? 16'sd32767 :
        (rounded5 < -28'sd32768) ? -16'sd32768 :
        rounded5[15:0];

    integer j;
    always @(posedge clk) begin
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            v4 <= 1'b0;
            v5 <= 1'b0;
            for (j = 0; j < 15; j = j + 1)
                history[j] <= 16'sd0;
        end else begin
            if (ready1) begin
                v1 <= in_valid;
                if (in_valid) begin
                    pair1[0] <= {in_sample[15], in_sample} +
                                {history[14][15], history[14]};
                    pair1[1] <= {history[0][15], history[0]} +
                                {history[13][15], history[13]};
                    pair1[2] <= {history[1][15], history[1]} +
                                {history[12][15], history[12]};
                    pair1[3] <= {history[2][15], history[2]} +
                                {history[11][15], history[11]};
                    pair1[4] <= {history[3][15], history[3]} +
                                {history[10][15], history[10]};
                    pair1[5] <= {history[4][15], history[4]} +
                                {history[9][15], history[9]};
                    pair1[6] <= {history[5][15], history[5]} +
                                {history[8][15], history[8]};
                    pair1[7] <= {history[6][15], history[6]} +
                                {history[7][15], history[7]};
                    for (j = 14; j > 0; j = j - 1)
                        history[j] <= history[j-1];
                    history[0] <= in_sample;
                end
            end

            if (ready2) begin
                v2 <= v1;
                if (v1)
                    partial2 <= group2;
            end

            if (ready3) begin
                v3 <= v2;
                if (v2)
                    partial3 <= group3;
            end

            if (ready4) begin
                v4 <= v3;
                if (v3)
                    accum4 <= partial2 + partial3;
            end

            if (ready5) begin
                v5 <= v4;
                if (v4)
                    d5 <= result5;
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