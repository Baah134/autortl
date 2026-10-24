`timescale 1ns/1ps
// @latency 9
module iterative_divider (
    input wire clk,
    input wire rst,
    input wire [7:0] dividend,
    input wire [7:0] divisor,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] quotient,
    output wire [7:0] remainder,
    output wire out_valid,
    input wire out_ready
);
    reg busy;
    reg out_valid_reg;
    reg [7:0] quotient_work;
    reg [8:0] remainder_work;
    reg [2:0] iteration;
    reg [7:0] quotient_reg;
    reg [7:0] remainder_reg;

    wire [8:0] trial_remainder;
    wire [8:0] divisor_ext;
    wire [8:0] next_remainder;
    wire [7:0] next_quotient;
    wire subtract;

    assign trial_remainder = {remainder_work[7:0], quotient_work[7]};
    assign divisor_ext = {1'b0, divisor};
    assign subtract = (trial_remainder >= divisor_ext);
    assign next_remainder = subtract
        ? trial_remainder - divisor_ext
        : trial_remainder;
    assign next_quotient = {quotient_work[6:0], subtract};

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            quotient_work <= 8'b0;
            remainder_work <= 9'b0;
            iteration <= 3'b0;
            quotient_reg <= 8'b0;
            remainder_reg <= 8'b0;
        end else if (busy) begin
            quotient_work <= next_quotient;
            remainder_work <= next_remainder;

            if (iteration == 3'd7) begin
                busy <= 1'b0;
                out_valid_reg <= 1'b1;
                quotient_reg <= next_quotient;
                remainder_reg <= next_remainder[7:0];
            end else begin
                iteration <= iteration + 1'b1;
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            quotient_work <= dividend;
            remainder_work <= 9'b0;
            iteration <= 3'b0;
            busy <= 1'b1;
        end
    end
endmodule