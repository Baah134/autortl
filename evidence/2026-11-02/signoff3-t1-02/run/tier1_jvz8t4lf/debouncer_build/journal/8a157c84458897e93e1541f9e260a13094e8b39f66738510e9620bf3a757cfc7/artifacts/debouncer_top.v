`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [2:0] count;

    wire count_carry = count[1] & count[0];
    wire terminal = count[2] & count_carry;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            count <= 3'b000;
        end else if (noisy == clean_reg) begin
            count <= 3'b000;
        end else begin
            count[0] <= ~count[0];
            count[1] <= count[1] ^ count[0];
            count[2] <= count[2] ^ count_carry;

            if (terminal)
                clean_reg <= noisy;
        end
    end
endmodule