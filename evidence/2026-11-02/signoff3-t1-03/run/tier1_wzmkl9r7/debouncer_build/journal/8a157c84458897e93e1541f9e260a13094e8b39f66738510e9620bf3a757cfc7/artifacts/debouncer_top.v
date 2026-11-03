`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg candidate;
    reg [2:0] counter;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            candidate <= 1'b0;
            counter   <= 3'd0;
        end else if (noisy != candidate) begin
            candidate <= noisy;
            counter   <= 3'd7;
        end else if (counter == 3'd1) begin
            clean_reg <= candidate;
            counter   <= 3'd0;
        end else if (counter != 3'd0) begin
            counter <= counter - 1'b1;
        end else begin
            clean_reg <= candidate;
        end
    end
endmodule