`timescale 1ns/1ps
// @latency 1
module uart_tx_core #(
    parameter integer DIV = 868
) (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] in_data,
    input  wire       in_valid,
    output wire       in_ready,
    output wire       tx
);

    reg       ready_reg;
    reg       tx_reg;
    reg       busy;
    reg [7:0] shift_reg;
    reg [3:0] bit_index;
    reg [12:0] bit_count;

    assign in_ready = ready_reg;
    assign tx       = tx_reg;

    always @(posedge clk) begin
        if (rst) begin
            ready_reg <= 1'b1;
            tx_reg    <= 1'b1;
            busy      <= 1'b0;
            shift_reg <= 8'b0;
            bit_index <= 4'b0;
            bit_count <= 13'b0;
        end else if (!busy) begin
            if (in_valid && ready_reg) begin
                ready_reg <= 1'b0;
                tx_reg    <= 1'b0;
                busy      <= 1'b1;
                shift_reg <= in_data;
                bit_index <= 4'd0;
                bit_count <= DIV;
            end
        end else if (bit_count > 13'd1) begin
            bit_count <= bit_count - 13'd1;
        end else if (bit_index == 4'd9) begin
            ready_reg <= 1'b1;
            tx_reg    <= 1'b1;
            busy      <= 1'b0;
            bit_count <= 13'b0;
        end else if (bit_index == 4'd8) begin
            tx_reg    <= 1'b1;
            bit_index <= bit_index + 4'd1;
            bit_count <= DIV;
        end else begin
            tx_reg    <= shift_reg[0];
            shift_reg <= {1'b0, shift_reg[7:1]};
            bit_index <= bit_index + 4'd1;
            bit_count <= DIV;
        end
    end

endmodule