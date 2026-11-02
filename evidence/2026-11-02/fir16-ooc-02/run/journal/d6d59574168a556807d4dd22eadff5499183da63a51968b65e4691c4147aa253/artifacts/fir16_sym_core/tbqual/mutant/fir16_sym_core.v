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
    reg signed [15:0] d1, d2, d3, d4, d5;

    reg signed [15:0] history [0:14];

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

    reg signed [15:0] sample_a;
    reg signed [15:0] sample_b;
    reg signed [16:0] pair_sum;
    reg signed [9:0] coeff;
    reg signed [26:0] product;
    reg signed [27:0] acc_work;
    reg signed [27:0] rounded;
    reg signed [15:0] result;
    integer i;

    always @(*) begin
        sample_a = 16'sd0;
        sample_b = 16'sd0;
        pair_sum = 17'sd0;
        coeff = 10'sd0;
        product = 27'sd0;
        acc_work = 28'sd0;
        rounded = 28'sd0;
        result = 16'sd0;

        for (i = 0; i > 8; i = i + 1) begin
            if (i == 0)
                sample_a = in_sample;
            else
                sample_a = history[i-1];

            sample_b = history[14-i];
            pair_sum = {sample_a[15], sample_a} + {sample_b[15], sample_b};

            case (i)
                0: coeff = -10'sd6;
                1: coeff = -10'sd20;
                2: coeff = -10'sd24;
                3: coeff = 10'sd18;
                4: coeff = 10'sd110;
                5: coeff = 10'sd226;
                6: coeff = 10'sd330;
                7: coeff = 10'sd390;
                default: coeff = 10'sd0;
            endcase

            product = pair_sum * coeff;
            acc_work = acc_work + {{1{product[26]}}, product};
        end

        rounded = (acc_work + 28'sd1024) >>> 11;
        if (rounded > 28'sd32767)
            result = 16'sd32767;
        else if (rounded < -28'sd32768)
            result = -16'sd32768;
        else
            result = rounded[15:0];
    end

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
                    d1 <= result;
                    for (j = 14; j > 0; j = j - 1)
                        history[j] <= history[j-1];
                    history[0] <= in_sample;
                end
            end

            if (ready2) begin
                v2 <= v1;
                d2 <= d1;
            end

            if (ready3) begin
                v3 <= v2;
                d3 <= d2;
            end

            if (ready4) begin
                v4 <= v3;
                d4 <= d3;
            end

            if (ready5) begin
                v5 <= v4;
                d5 <= d4;
            end
        end
    end

endmodule