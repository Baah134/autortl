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

reg busy;
reg out_valid_reg;
reg [3:0] i;
reg signed [17:0] x_state;
reg signed [17:0] y_state;
reg [19:0] z_state;
wire signed [17:0] x_shift;
wire signed [17:0] y_shift;

assign x_shift = x_state >>> i;
assign y_shift = y_state >>> i;

assign in_ready = !busy && !out_valid_reg;
assign out_valid = out_valid_reg;
assign iter = i;
assign x = x_state;
assign y = y_state;

always @(posedge clk) begin
    if (rst) begin
        busy <= 1'b0;
        out_valid_reg <= 1'b0;
        i <= 4'd0;
        x_state <= 18'd0;
        y_state <= 18'd0;
        z_state <= 20'd0;
    end else if (busy) begin
        if (!z_state[19]) begin
            x_state <= x_state - y_shift;
            y_state <= y_state + x_shift;
            z_state <= z_state - atan_val;
        end else begin
            x_state <= x_state + y_shift;
            y_state <= y_state - x_shift;
            z_state <= z_state + atan_val;
        end

        i <= i + 4'd1;
        if (i == 4'd15) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b1;
        end
    end else if (out_valid_reg) begin
        if (out_ready)
            out_valid_reg <= 1'b0;
    end else if (in_valid) begin
        x_state <= x0;
        y_state <= 18'd0;
        z_state <= z0;
        i <= 4'd0;
        busy <= 1'b1;
    end
end

endmodule