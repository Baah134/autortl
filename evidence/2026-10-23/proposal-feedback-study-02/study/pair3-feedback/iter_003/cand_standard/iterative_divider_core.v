`timescale 1ns/1ps
// @latency 9
module iterative_divider_core #(
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst,
    input wire [WIDTH-1:0] dividend,
    input wire [WIDTH-1:0] divisor,
    input wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] quotient,
    output wire [WIDTH-1:0] remainder,
    output wire out_valid,
    input wire out_ready
);

    localparam COUNT_WIDTH = $clog2(WIDTH + 1);

    reg busy;
    reg out_valid_reg;
    reg [WIDTH-1:0] dividend_reg;
    reg [WIDTH-1:0] divisor_reg;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH:0] remainder_work;
    reg [COUNT_WIDTH-1:0] iteration;

    reg [WIDTH-1:0] quotient_reg;
    reg [WIDTH-1:0] remainder_reg;

    wire [WIDTH:0] trial_remainder;
    wire [WIDTH+1:0] subtract_result;
    wire no_borrow;
    wire [WIDTH:0] next_remainder;
    wire [WIDTH-1:0] next_quotient;

    assign trial_remainder = {
        remainder_work[WIDTH-1:0],
        quotient_work[WIDTH-1]
    };

    assign subtract_result =
        {1'b0, trial_remainder} - {{2{1'b0}}, divisor_reg};
    assign no_borrow = ~subtract_result[WIDTH+1];

    assign next_remainder = no_borrow
        ? subtract_result[WIDTH:0]
        : trial_remainder;

    assign next_quotient = (quotient_work << 1) | no_borrow;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            dividend_reg <= {WIDTH{1'b0}};
            divisor_reg <= {WIDTH{1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            remainder_work <= {(WIDTH+1){1'b0}};
            iteration <= {COUNT_WIDTH{1'b0}};
            quotient_reg <= {WIDTH{1'b0}};
            remainder_reg <= {WIDTH{1'b0}};
        end else if (busy) begin
            quotient_work <= next_quotient;
            remainder_work <= next_remainder;

            if (iteration == 1) begin
                busy <= 1'b0;
                out_valid_reg <= 1'b1;
                quotient_reg <= next_quotient;
                remainder_reg <= next_remainder[WIDTH-1:0];
            end else begin
                iteration <= iteration - 1'b1;
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            dividend_reg <= dividend;
            divisor_reg <= divisor;
            quotient_work <= dividend;
            remainder_work <= {(WIDTH+1){1'b0}};
            iteration <= WIDTH;
            busy <= 1'b1;
        end
    end

endmodule