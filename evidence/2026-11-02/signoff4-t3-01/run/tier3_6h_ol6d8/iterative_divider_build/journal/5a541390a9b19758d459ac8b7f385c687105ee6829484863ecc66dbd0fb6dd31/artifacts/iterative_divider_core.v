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

    reg busy;
    reg result_valid;
    reg [WIDTH-1:0] quotient_result;
    reg [WIDTH-1:0] remainder_result;

    reg [WIDTH-1:0] divisor_reg;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH:0] remainder_work;
    reg [4:0] iteration;

    wire [WIDTH:0] trial_remainder;
    wire [WIDTH:0] divisor_extended;
    wire subtract_divisor;
    wire [WIDTH:0] remainder_step;
    wire [WIDTH-1:0] quotient_step;

    assign in_ready = !busy && !result_valid;
    assign out_valid = result_valid;
    assign quotient = quotient_result;
    assign remainder = remainder_result;

    assign trial_remainder = {remainder_work[WIDTH-1:0], quotient_work[WIDTH-1]};
    assign divisor_extended = {1'b0, divisor_reg};
    assign subtract_divisor = (trial_remainder >= divisor_extended);
    assign remainder_step = subtract_divisor
                          ? (trial_remainder - divisor_extended)
                          : trial_remainder;
    assign quotient_step = (quotient_work << 1)
                         | {{(WIDTH-1){1'b0}}, subtract_divisor};

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            result_valid <= 1'b0;
            quotient_result <= {WIDTH{1'b0}};
            remainder_result <= {WIDTH{1'b0}};
            divisor_reg <= {WIDTH{1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            remainder_work <= {(WIDTH+1){1'b0}};
            iteration <= 5'd0;
        end else begin
            if (busy) begin
                quotient_work <= quotient_step;
                remainder_work <= remainder_step;
                iteration <= iteration + 1'b1;

                if (iteration == WIDTH - 1) begin
                    quotient_result <= quotient_step;
                    remainder_result <= remainder_step[WIDTH-1:0];
                    busy <= 1'b0;
                    result_valid <= 1'b1;
                end
            end else if (result_valid) begin
                if (out_ready)
                    result_valid <= 1'b0;
            end else if (in_valid && in_ready) begin
                divisor_reg <= divisor;
                quotient_work <= dividend;
                remainder_work <= {(WIDTH+1){1'b0}};
                iteration <= 5'd0;
                busy <= 1'b1;
            end
        end
    end

endmodule