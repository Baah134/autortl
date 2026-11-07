`timescale 1ns/1ps
// @latency 3
module signed_fir4_core (
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
    reg signed [7:0] x_prev1, x_prev2, x_prev3;

    wire r3 = !v3 || out_ready;
    wire r2 = !v2 || r3;
    wire r1 = !v1 || r2;

    assign in_ready = r1;
    assign out_valid = v3;
    assign out_data = d3;

    wire signed [9:0] x_10 =
        {{2{x[7]}}, x};
    wire signed [10:0] x_prev1_11 =
        {{3{x_prev1[7]}}, x_prev1};
    wire signed [10:0] x_prev2_11 =
        {{3{x_prev2[7]}}, x_prev2};
    wire signed [8:0] x_prev3_9 =
        {{1{x_prev3[7]}}, x_prev3};

    wire signed [9:0] term0 =
        x_10 * 10'sd3;
    wire signed [10:0] term1 =
        x_prev1_11 * 11'sd5;
    wire signed [10:0] term2 =
        x_prev2_11 * 11'sd7;
    wire signed [8:0] term3 =
        x_prev3_9 * 9'sd2;

    wire signed [10:0] sum1 =
        {{1{term0[9]}}, term0} - term1;
    wire signed [11:0] sum2 =
        {{1{sum1[10]}}, sum1} + {{1{term2[10]}}, term2};
    wire signed [12:0] fir_result =
        {{1{sum2[11]}}, sum2} - {{4{term3[8]}}, term3};

    always @(posedge clk) begin
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            x_prev1 <= 8'sd0;
            x_prev2 <= 8'sd0;
            x_prev3 <= 8'sd0;
        end else begin
            if (r3) begin
                v3 <= v2;
                d3 <= d2;
            end

            if (r2) begin
                v2 <= v1;
                d2 <= d1;
            end

            if (r1) begin
                v1 <= in_valid;
                if (in_valid) begin
                    d1 <= fir_result;
                    x_prev3 <= x_prev2;
                    x_prev2 <= x_prev1;
                    x_prev1 <= x;
                end
            end
        end
    end

endmodule

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
    signed_fir4_core u_signed_fir4_core (
        .clk(clk),
        .rst(rst),
        .x(x),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule