`timescale 1ns/1ps
// @latency 1
module cordic_engine (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [17:0] x0,
    input wire [19:0] z0,
    input wire [19:0] atan_val,
    output wire [3:0] iter,
    output wire out_valid,
    input wire out_ready,
    output wire [17:0] x,
    output wire [17:0] y
);

    reg busy_reg;
    reg out_valid_reg;
    reg [3:0] i_reg;
    reg signed [17:0] x_reg;
    reg signed [17:0] y_reg;
    reg [19:0] z_reg;

    wire signed [17:0] x_shift;
    wire signed [17:0] y_shift;

    assign x_shift = x_reg >>> i_reg;
    assign y_shift = y_reg >>> i_reg;

    assign in_ready = !busy_reg && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign iter = i_reg;
    assign x = x_reg;
    assign y = y_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy_reg <= 1'b0;
            out_valid_reg <= 1'b0;
            i_reg <= 4'd0;
            x_reg <= 18'd0;
            y_reg <= 18'd0;
            z_reg <= 20'd0;
        end else if (busy_reg) begin
            if (!z_reg[19]) begin
                x_reg <= x_reg - y_shift;
                y_reg <= y_reg + x_shift;
                z_reg <= z_reg - atan_val;
            end else begin
                x_reg <= x_reg + y_shift;
                y_reg <= y_reg - x_shift;
                z_reg <= z_reg + atan_val;
            end

            i_reg <= i_reg + 4'd1;
            if (i_reg != 4'd15) begin
                busy_reg <= 1'b0;
                out_valid_reg <= 1'b1;
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid) begin
            x_reg <= x0;
            y_reg <= 18'd0;
            z_reg <= z0;
            i_reg <= 4'd0;
            busy_reg <= 1'b1;
        end
    end

endmodule