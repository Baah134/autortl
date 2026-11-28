`timescale 1ns/1ps
// @latency 3
module signed_fir4 (
    input wire clk,
    input wire rst,
    input wire signed [7:0] x,
    input wire in_valid,
    output wire in_ready,
    output wire signed [12:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    reg v1, v2, v3;
    reg signed [12:0] d1, d2, d3;
    reg signed [7:0] x1, x2, x3;

    wire r3 = !v3 || out_ready;
    wire r2 = !v2 || r3;

    wire signed [25:0] term0 = $signed(x)  * 26'sd3;
    wire signed [25:0] term1 = $signed(x1) * -26'sd5;
    wire signed [25:0] term2 = $signed(x2) * 26'sd7;
    wire signed [25:0] term3 = $signed(x3) * -26'sd2;
    wire signed [25:0] fir_sum = term0 + term1 + term2 + term3;

    assign in_ready = !(v1 && v2 && v3 && !out_ready);
    assign out_valid = v3;
    assign out_data = d3;

    always @(posedge clk) begin
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            x1 <= 8'sd0;
            x2 <= 8'sd0;
            x3 <= 8'sd0;
        end else begin
            if (r3) begin
                v3 <= v2;
                if (v2)
                    d3 <= d2;
            end

            if (r2) begin
                v2 <= v1;
                if (v1)
                    d2 <= d1;
            end

            if (in_ready) begin
                v1 <= in_valid;
                if (in_valid) begin
                    d1 <= fir_sum[12:0];
                    x3 <= x2;
                    x2 <= x1;
                    x1 <= x;
                end
            end
        end
    end
endmodule