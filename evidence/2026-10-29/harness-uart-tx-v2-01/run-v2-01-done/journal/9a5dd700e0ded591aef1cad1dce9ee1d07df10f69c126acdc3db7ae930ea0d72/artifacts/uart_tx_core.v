`timescale 1ns/1ps
// @latency 1
module uart_tx_core #(
    parameter DIV = 868
) (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire tx
);

    localparam integer STOP = DIV - DIV/16;

    reg [7:0] data_reg;
    reg [3:0] bit_index;
    reg [12:0] bit_count;
    reg busy;
    reg tx_reg;
    reg in_ready_reg;

    assign tx = tx_reg;
    assign in_ready = in_ready_reg;

    always @(posedge clk) begin
        if (rst) begin
            data_reg <= 8'd0;
            bit_index <= 4'd0;
            bit_count <= 13'd0;
            busy <= 1'b0;
            tx_reg <= 1'b1;
            in_ready_reg <= 1'b1;
        end else if (!busy) begin
            tx_reg <= 1'b1;
            in_ready_reg <= 1'b1;
            if (in_valid && in_ready_reg) begin
                data_reg <= in_data;
                bit_index <= 4'd0;
                bit_count <= DIV - 1;
                busy <= 1'b1;
                tx_reg <= 1'b0;
                in_ready_reg <= 1'b0;
            end
        end else if (bit_count != 0) begin
            bit_count <= bit_count - 1'b1;
        end else if (bit_index == 4'd9) begin
            busy <= 1'b0;
            tx_reg <= 1'b1;
            in_ready_reg <= 1'b1;
        end else begin
            bit_index <= bit_index + 1'b1;
            if (bit_index == 4'd8) begin
                tx_reg <= 1'b1;
                bit_count <= STOP - 1;
            end else begin
                tx_reg <= data_reg[bit_index];
                bit_count <= DIV - 1;
            end
        end
    end

endmodule