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
    reg out_valid_reg;

    reg [WIDTH-1:0] divisor_reg;
    reg [WIDTH-1:0] quotient_work;
    reg [WIDTH-1:0] remainder_work;
    reg [WIDTH-1:0] quotient_reg;
    reg [WIDTH-1:0] remainder_reg;
    reg [31:0] iteration_count;

    wire [WIDTH:0] trial_remainder;
    wire [WIDTH:0] divisor_extended;
    wire [WIDTH:0] difference;
    wire [WIDTH-1:0] next_remainder;
    wire next_quotient_bit;
    wire [WIDTH-1:0] shifted_quotient;

    assign trial_remainder = {remainder_work, quotient_work[WIDTH-1]};
    assign divisor_extended = {1'b0, divisor_reg};
    assign difference = trial_remainder - divisor_extended;
    assign next_quotient_bit = (trial_remainder >= divisor_extended);
    assign next_remainder = next_quotient_bit
                          ? difference[WIDTH-1:0]
                          : trial_remainder[WIDTH-1:0];
    assign shifted_quotient = (quotient_work << 1) | next_quotient_bit;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign quotient = quotient_reg;
    assign remainder = remainder_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            divisor_reg <= {WIDTH{1'b0}};
            quotient_work <= {WIDTH{1'b0}};
            remainder_work <= {WIDTH{1'b0}};
            quotient_reg <= {WIDTH{1'b0}};
            remainder_reg <= {WIDTH{1'b0}};
            iteration_count <= 32'd0;
        end else if (busy) begin
            quotient_work <= shifted_quotient;
            remainder_work <= next_remainder;

            if (iteration_count == 32'd0) begin
                busy <= 1'b0;
                out_valid_reg <= 1'b1;
                quotient_reg <= shifted_quotient;
                remainder_reg <= next_remainder;
            end else begin
                iteration_count <= iteration_count - 32'd1;
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid) begin
            busy <= 1'b1;
            divisor_reg <= divisor;
            quotient_work <= dividend;
            remainder_work <= {WIDTH{1'b0}};
            iteration_count <= WIDTH - 1;
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 9
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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
    iterative_divider_core #(.WIDTH(8)) u_iterative_divider_core (
        .clk(clk),
        .rst(rst),
        .dividend(dividend),
        .divisor(divisor),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .quotient(quotient),
        .remainder(remainder),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule