`timescale 1ns/1ps
// @latency 1
module counter8 (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);
    reg [7:0] count_reg;

    assign count = count_reg;

    always @(posedge clk) begin
        if (rst) begin
            count_reg <= 8'd0;
        end else if (enable) begin
            count_reg[0] <= ~count_reg[0];
            count_reg[1] <= count_reg[1] ^ count_reg[0];
            count_reg[2] <= count_reg[2] ^ (&count_reg[1:0]);
            count_reg[3] <= count_reg[3] ^ (&count_reg[2:0]);
            count_reg[4] <= count_reg[4] ^ (&count_reg[3:0]);
            count_reg[5] <= count_reg[5] ^ (&count_reg[4:0]);
            count_reg[6] <= count_reg[6] ^ (&count_reg[5:0]);
            count_reg[7] <= count_reg[7] ^ (&count_reg[6:0]);
        end
    end
endmodule