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

    reg signed [7:0] history1;
    reg signed [7:0] history2;
    reg signed [7:0] history3;

    reg valid1;
    reg valid2;
    reg valid3;

    reg signed [12:0] data1;
    reg signed [12:0] data2;
    reg signed [12:0] data3;

    wire ready3 = !valid3 || out_ready;
    wire ready2 = !valid2 || ready3;
    wire ready1 = !valid1 || ready2;

    assign in_ready = ready1;
    assign out_valid = valid3;
    assign out_data = data3;

    wire signed [15:0] x_wide = {{8{x[7]}}, x};
    wire signed [15:0] history1_wide = {{8{history1[7]}}, history1};
    wire signed [15:0] history2_wide = {{8{history2[7]}}, history2};
    wire signed [15:0] history3_wide = {{8{history3[7]}}, history3};

    wire signed [15:0] fir_value =
        (x_wide * 16'sd3)
        - (history1_wide * 16'sd5)
        + (history2_wide * 16'sd7)
        - (history3_wide * 16'sd2);

    always @(posedge clk) begin
        if (rst) begin
            history1 <= 8'sd0;
            history2 <= 8'sd0;
            history3 <= 8'sd0;
            valid1 <= 1'b0;
            valid2 <= 1'b0;
            valid3 <= 1'b0;
        end else begin
            if (ready1) begin
                valid1 <= in_valid;
                if (in_valid) begin
                    data1 <= fir_value[12:0];
                    history3 <= history2;
                    history2 <= history1;
                    history1 <= x;
                end
            end

            if (ready2) begin
                valid2 <= valid1;
                if (valid1)
                    data2 <= data1;
            end

            if (ready3) begin
                valid3 <= valid2;
                if (valid2)
                    data3 <= data2;
            end
        end
    end

endmodule