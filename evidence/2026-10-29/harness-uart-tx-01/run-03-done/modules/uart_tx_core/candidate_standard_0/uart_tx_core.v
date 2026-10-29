`timescale 1ns/1ps
// @latency 1
module uart_tx_core #(
    parameter integer DIV = 868
) (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire tx
);

    reg ready_reg;
    reg tx_reg;
    reg [7:0] data_reg;
    reg [3:0] bit_index;
    reg [12:0] bit_count;

    assign in_ready = ready_reg;
    assign tx = tx_reg;

    always @(posedge clk) begin
        if (rst) begin
            ready_reg <= 1'b1;
            tx_reg <= 1'b1;
            data_reg <= 8'b0;
            bit_index <= 4'b0;
            bit_count <= 13'b0;
        end else if (ready_reg) begin
            if (in_valid) begin
                data_reg <= in_data;
                ready_reg <= 1'b0;
                tx_reg <= 1'b0;
                bit_index <= 4'd0;
                bit_count <= DIV;
            end
        end else begin
            if (bit_count > 13'd1) begin
                bit_count <= bit_count - 13'd1;
            end else begin
                bit_count <= DIV;
                if (bit_index == 4'd9) begin
                    ready_reg <= 1'b1;
                    tx_reg <= 1'b1;
                end else begin
                    bit_index <= bit_index + 4'd1;
                    if (bit_index < 4'd8)
                        tx_reg <= data_reg[bit_index];
                    else
                        tx_reg <= 1'b1;
                end
            end
        end
    end

endmodule